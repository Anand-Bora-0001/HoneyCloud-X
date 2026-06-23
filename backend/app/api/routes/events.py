"""
Event routes: ingest, list, clear, stream, simulate.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Header, BackgroundTasks
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
import asyncio
import json
import random
import logging
from collections import deque

from ..deps import get_current_user, get_admin_user, get_db
from ...services.geo_service import get_location_from_ip, get_real_client_ip, get_country_flag
from ...config import settings
from ...deception_env.scenario_engine import evaluate_scenario

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Events"])

# Bounded in-memory event storage for fallbacks
attack_events = deque(maxlen=1000)

class EventBroadcaster:
    def __init__(self):
        self.queues = []
    
    def add_queue(self):
        q = asyncio.Queue()
        self.queues.append(q)
        return q
        
    def remove_queue(self, q):
        if q in self.queues:
            self.queues.remove(q)
            
    def broadcast(self, event):
        for q in self.queues:
            q.put_nowait(event)

broadcaster = EventBroadcaster()


def process_event_async(event: Dict, source_ip: str, org_id: int, service_id: int, service_name: str, x_api_key: str, route_decision: Dict):
    from ...database import SessionLocal
    from ...models import AttackEvent
    from ...deception_engine import ThreatRoutingEngine
    from ...deception_engine.persona_engine import PersonaEngine
    
    db = SessionLocal()
    try:
        location_data = get_location_from_ip(source_ip)

        # ML prediction (if available)
        ml_prediction = None
        try:
            from ...ml_engine import ml_engine
            if ml_engine:
                temp_event = {
                    "service": service_name,
                    "source_ip": source_ip,
                    "source_port": event.get("source_port", 0),
                    "username": event.get("username"),
                    "password": event.get("password"),
                    "command": event.get("command") or event.get("endpoint"),
                    "payload": event.get("payload"),
                    "method": event.get("method", "UNKNOWN"),
                    "endpoint": event.get("endpoint"),
                    "severity": event.get("severity", "MEDIUM"),
                    "timestamp": event.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    "location": location_data
                }
                ml_prediction = ml_engine.predict_threat(temp_event)
        except Exception as ml_error:
            logger.warning(f"ML prediction skipped: {ml_error}")

        # Routing decision is now calculated synchronously in ingest_event
        # We just use the passed route_decision

        # Enrich event
        enriched_event = {
            "timestamp": event.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "service": service_name,
            "source_ip": source_ip,
            "source_port": event.get("source_port", 0),
            "username": event.get("username"),
            "password": event.get("password"),
            "command": event.get("command") or event.get("endpoint"),
            "payload": event.get("payload"),
            "method": event.get("method", "UNKNOWN"),
            "endpoint": event.get("endpoint"),
            "severity": ml_prediction.threat_level if ml_prediction else event.get("severity", "MEDIUM"),
            "ai_label": "ml_predicted" if ml_prediction else event.get("ai_label", "anomaly"),
            "threat_score": route_decision["threat_score"],
            "ml_confidence": ml_prediction.confidence if ml_prediction else 0.0,
            "anomaly_score": ml_prediction.anomaly_score if ml_prediction else 0.0,
            "location": {
                'city': location_data['city'],
                'country': location_data['country'],
                'country_code': location_data['country_code'],
                'flag': get_country_flag(location_data['country_code']),
                'isp': location_data['isp'],
                'region': location_data['region'],
                'lat': location_data.get('lat', 0.0),
                'lng': location_data.get('lng', 0.0),
            },
            "event_metadata": event.get("metadata", {}),
            "session_id": route_decision["session_id"],
            "recommended_route": route_decision["recommended_route"]
        }

        # Save to database
        db_event = AttackEvent(
            organization_id=org_id,
            service_name=enriched_event["service"],
            source_ip=source_ip,
            source_port=enriched_event.get("source_port", 0),
            endpoint=enriched_event.get("endpoint"),
            method=enriched_event.get("method"),
            username=enriched_event.get("username"),
            password=enriched_event.get("password"),
            command=enriched_event.get("command"),
            payload=enriched_event.get("payload"),
            severity=enriched_event["severity"],
            ai_label=enriched_event["ai_label"],
            threat_score=enriched_event["threat_score"],
            location=enriched_event["location"],
            event_metadata=enriched_event.get("event_metadata", {})
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        enriched_event["id"] = db_event.id

        attack_events.append(enriched_event)
        broadcaster.broadcast(enriched_event)

        # Update Persona async
        try:
            from ...models import AttackerProfile, DeceptionAction, DeceptionSession
            profile = db.query(AttackerProfile).filter(
                AttackerProfile.source_ip == source_ip, 
                AttackerProfile.organization_id == org_id
            ).first()
            if profile:
                # Find all actions associated with this attacker's sessions
                sessions = db.query(DeceptionSession).filter(DeceptionSession.source_ip == source_ip).all()
                session_ids = [s.session_id for s in sessions]
                if session_ids:
                    actions = db.query(DeceptionAction).filter(DeceptionAction.session_id.in_(session_ids)).all()
                    PersonaEngine.update_profile_persona(profile, actions)
                    db.commit()
                    
                    # Phase 4: Run Deep Investigation
                    try:
                        from ...investigation_engine import InvestigationService
                        InvestigationService.run_investigation(db, profile.id)
                    except Exception as inv_err:
                        logger.error(f"Investigation Service failed: {inv_err}")
                        
        except Exception as pe:
            logger.warning(f"Persona classification failed: {pe}")
            db.rollback()

        # Trigger alerts for critical events
        if enriched_event['severity'] in ['CRITICAL', 'HIGH'] or route_decision['recommended_route'] == 'DECEPTION':
            try:
                from ...alert_system import handle_attack_event
                enriched_event['organization_id'] = db_event.organization_id
                handle_attack_event(enriched_event, db)
            except Exception:
                pass

    except Exception as e:
        logger.error(f"❌ Background processing failed: {e}")
    finally:
        db.close()


@router.post("/ingest")
async def ingest_event(
    event: Dict, 
    request: Request, 
    background_tasks: BackgroundTasks, 
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    Ingest attack data from honeypots.
    Requires X-API-Key header.
    """
    from ...database import get_db
    from ...models import Organization, Service

    if not x_api_key:
        raise HTTPException(status_code=401, detail="API Key required")
        
    db = None
    try:
        db = next(get_db())
        service_record = db.query(Service).filter(Service.api_key == x_api_key).first()
        
        if not service_record:
            if x_api_key == "hc_live_fsj-onia9stXSc2HgIuUDqfwR_f5Oe0Q4sTZTMhBku0":
                org = db.query(Organization).first()
                if not org:
                    org = Organization(name="Demo Organization", slug="demo-org", email="demo@honeycloud.local", plan="free", is_trial=True)
                    db.add(org)
                    db.commit()
                    db.refresh(org)
                service_record = Service(name="Demo Service", slug="demo-service", api_key=x_api_key, organization_id=org.id)
                db.add(service_record)
                db.commit()
                db.refresh(service_record)
            else:
                raise HTTPException(status_code=401, detail="Invalid API Key")
        
        org_id = service_record.organization_id
        service_id = service_record.id
        service_name = service_record.name
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DB Error during auth: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if db:
            db.close()

    source_ip = event.get("source_ip") or get_real_client_ip(request)
    
    # Fast-path routing evaluation
    from ...database import SessionLocal
    from ...deception_engine import ThreatRoutingEngine
    
    route_decision = {"recommended_route": "CONTINUE", "session_id": None, "threat_score": 0.0}
    routing_db = SessionLocal()
    try:
        routing_engine = ThreatRoutingEngine(routing_db)
        
        # Determine action_type quickly
        action_type = "VISIT"
        event_metadata = event.get("metadata", {})
        event_type = event_metadata.get("event_type", "")
        
        if event_type == "ACCOUNT_ENUMERATION":
            action_type = "ACCOUNT_ENUMERATION"
        elif event_type == "FAILED_LOGIN":
            # Escalate to CREDENTIAL_STUFFING if attempt count is high
            attempt_count = event_metadata.get("attempt_count", 1)
            if attempt_count >= 5:
                action_type = "CREDENTIAL_STUFFING"
            else:
                action_type = "AUTH_FAILURE"
        elif event_type == "SUCCESSFUL_LOGIN":
            action_type = "VISIT"  # Legitimate login is just a visit
        elif event.get("severity") in ["HIGH", "CRITICAL"]:
            if "login" in str(event.get("endpoint", "")).lower() or event.get("username"):
                action_type = "AUTH_FAILURE"
            elif ".env" in str(event.get("endpoint", "")):
                action_type = "DIRECTORY_SCAN"
            else:
                action_type = "SCAN"
                
        route_decision = routing_engine.evaluate_request(
            source_ip=source_ip,
            endpoint=event.get("endpoint", ""),
            method=event.get("method", "GET"),
            payload=str(event.get("payload") or ""),
            organization_id=org_id,
            service_id=service_id,
            user_agent=event.get("metadata", {}).get("user_agent", ""),
            action_type=action_type
        )
    except Exception as e:
        logger.error(f"Routing evaluation failed: {e}")
    finally:
        routing_db.close()

    background_tasks.add_task(process_event_async, event, source_ip, org_id, service_id, service_name, x_api_key, route_decision)
    
    return {
        "status": "received", 
        "message": "Event queued for processing",
        "recommended_route": route_decision.get("recommended_route", "CONTINUE"),
        "session_id": route_decision.get("session_id"),
        "redirect_url": evaluate_scenario(event.get("endpoint", ""), event.get("payload", ""))
    }


@router.get("/events")
def get_events(
    limit: int = 50,
    service: Optional[str] = None,
    severity: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get attack events with optional filters"""
    try:
        from ...models import AttackEvent, User

        if db is None:
            raise Exception("Database not available")

        user = db.query(User).filter(User.username == current_user["username"]).first()
        if not user:
            raise Exception("User not found in database")

        query = db.query(AttackEvent).filter(AttackEvent.organization_id == user.organization_id, AttackEvent.is_deleted == False)
        if service:
            query = query.filter(AttackEvent.service_name == service)
        if severity:
            query = query.filter(AttackEvent.severity == severity)

        events = query.order_by(AttackEvent.timestamp.desc()).limit(limit).all()

        result = []
        for event in events:
            result.append({
                "id": event.id,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "service": event.service_name,
                "source_ip": event.source_ip,
                "source_port": event.source_port,
                "username": event.username,
                "password": event.password,
                "command": event.command,
                "endpoint": event.endpoint,
                "method": event.method,
                "payload": event.payload,
                "severity": event.severity,
                "ai_label": event.ai_label,
                "threat_score": event.threat_score,
                "location": event.location,
                "event_metadata": event.event_metadata
            })

        return result

    except Exception as e:
        logger.warning(f"DB query failed ({e}), using in-memory events")
        filtered_events = list(attack_events)
        if service:
            filtered_events = [ev for ev in filtered_events if ev.get('service') == service]
        if severity:
            filtered_events = [ev for ev in filtered_events if ev.get('severity') == severity]
        return filtered_events[-limit:]


@router.delete("/events/clear")
def clear_events(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear all attack events for the current organization"""
    try:
        from ...models import AttackEvent, User, DeceptionSession, DeceptionAction, AttackerProfile, FileUploadAttempt, InvestigationReport
        user = db.query(User).filter(User.username == current_user["username"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Instead of deleting, we SOFT DELETE them to move to Recycle Bin
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        # We don't need to delete child records anymore, since the parent is just soft-deleted.
        # But for consistency, we should mark everything soft-deleted if needed.
        # However, AttackerProfile and DeceptionSession now have is_deleted columns.
        
        db.query(AttackEvent).filter(AttackEvent.organization_id == user.organization_id).update({"is_deleted": True, "deleted_at": now}, synchronize_session=False)
        db.query(DeceptionSession).filter(DeceptionSession.organization_id == user.organization_id).update({"is_deleted": True, "deleted_at": now}, synchronize_session=False)
        db.query(AttackerProfile).filter(AttackerProfile.organization_id == user.organization_id).update({"is_deleted": True, "deleted_at": now}, synchronize_session=False)
        
        # Also softly delete associated investigation reports
        profile_ids = [p.id for p in db.query(AttackerProfile.id).filter(AttackerProfile.organization_id == user.organization_id).all()]
        if profile_ids:
            db.query(InvestigationReport).filter(InvestigationReport.attacker_profile_id.in_(profile_ids)).update({"is_deleted": True, "deleted_at": now}, synchronize_session=False)
            
        # Log to AuditLog
        from ...models import AuditLog
        audit = AuditLog(
            organization_id=user.organization_id,
            user_id=user.id,
            action="Reset Demo Environment",
            records_removed=0, # It's a bulk reset
            details={"type": "soft_delete"}
        )
        db.add(audit)
        
        db.commit()

        if current_user.get("role") == "admin":
            attack_events.clear()

        # Invalidate stats cache
        try:
            from ...core.cache import cache_delete
            cache_delete(f"stats:{current_user['username']}")
        except Exception:
            pass
            
        return {"status": "success", "cleared": "all"}
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to clear events: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear events")

@router.post("/archive")
def archive_old_events(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Move old data to recycle bin based on retention policies"""
    try:
        from ...models import AttackEvent, User, AuditLog, InvestigationReport, AttackerProfile
        user = db.query(User).filter(User.username == current_user["username"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        
        # Policies: Events (30d), Investigations (90d)
        events_cutoff = now - timedelta(days=30)
        inv_cutoff = now - timedelta(days=90)
        
        events_archived = db.query(AttackEvent).filter(
            AttackEvent.organization_id == user.organization_id,
            AttackEvent.timestamp < events_cutoff,
            AttackEvent.is_deleted == False
        ).update({"is_deleted": True, "deleted_at": now}, synchronize_session=False)
        
        inv_archived = db.query(InvestigationReport).filter(
            InvestigationReport.organization_id == user.organization_id,
            InvestigationReport.generated_at < inv_cutoff,
            InvestigationReport.is_deleted == False
        ).update({"is_deleted": True, "deleted_at": now}, synchronize_session=False)
        
        total = events_archived + inv_archived
        
        if total > 0:
            audit = AuditLog(
                organization_id=user.organization_id,
                user_id=user.id,
                action="Archive Old Events",
                records_removed=total,
                details={"events": events_archived, "investigations": inv_archived}
            )
            db.add(audit)
            db.commit()
            
        return {"status": "success", "archived": total}
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to archive events: {e}")
        raise HTTPException(status_code=500, detail="Failed to archive events")


@router.get("/events/stream")
async def event_stream(current_user: dict = Depends(get_current_user)):
    """Server-Sent Events endpoint for real-time updates"""
    async def event_generator():
        q = broadcaster.add_queue()
        try:
            while True:
                event = await q.get()
                yield {"event": "new_attack", "data": json.dumps(event)}
        except asyncio.CancelledError:
            pass
        finally:
            broadcaster.remove_queue(q)

    return EventSourceResponse(event_generator())


@router.get("/stats")
def get_statistics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics (cached for 10s)"""
    from ...core.cache import cache_get_json, cache_set_json
    from datetime import timedelta

    # Check cache first
    cache_key = f"stats:{current_user.get('username', 'anon')}"
    cached = cache_get_json(cache_key)
    if cached:
        return cached

    try:
        from ...models import AttackEvent, User, DeceptionSession, AttackerProfile, DeceptionAction

        if db is None:
            raise Exception("Database not available")

        user = db.query(User).filter(User.username == current_user["username"]).first()
        if not user:
            raise Exception("User not found in database")

        events = db.query(AttackEvent).filter(
            AttackEvent.organization_id == user.organization_id,
            AttackEvent.is_deleted == False
        ).all()

        service_counts = {}
        severity_counts = {}
        label_counts = {}
        for event in events:
            s = event.service_name or 'UNKNOWN'
            service_counts[s] = service_counts.get(s, 0) + 1
            sv = event.severity or 'UNKNOWN'
            severity_counts[sv] = severity_counts.get(sv, 0) + 1
            lbl = event.ai_label or 'unknown'
            label_counts[lbl] = label_counts.get(lbl, 0) + 1

        unique_ips = len(set(e.source_ip for e in events if e.source_ip))
        avg_ml = sum(e.threat_score for e in events if e.threat_score is not None) / len(events) if events else 0.0
        active_services = len(set(e.service_name for e in events if e.service_name))

        # Hourly data
        now = datetime.now(timezone.utc)
        hourly_data = []
        hourly_labels = []
        for i in range(6, -1, -1):
            hour_time = now - timedelta(hours=i)
            hourly_labels.append(hour_time.strftime("%H:00"))
            count = 0
            for e in events:
                if e.timestamp:
                    evt_time = e.timestamp
                    if evt_time.tzinfo is None:
                        evt_time = evt_time.replace(tzinfo=timezone.utc)
                    if evt_time.hour == hour_time.hour and (now - evt_time).days == 0:
                        count += 1
            hourly_data.append(count)

        # Deception Metrics
        active_sessions = db.query(DeceptionSession).filter(
            DeceptionSession.organization_id == user.organization_id,
            DeceptionSession.status == "ACTIVE",
            DeceptionSession.is_deleted == False
        ).count()
        high_risk_sessions = db.query(DeceptionSession).filter(
            DeceptionSession.organization_id == user.organization_id,
            DeceptionSession.risk_level.in_(["HIGH", "CRITICAL"]),
            DeceptionSession.is_deleted == False
        ).count()
        total_profiles = db.query(AttackerProfile).filter(
            AttackerProfile.organization_id == user.organization_id,
            AttackerProfile.is_deleted == False
        ).count()

        trapped_sessions = db.query(DeceptionSession).filter(
            DeceptionSession.organization_id == user.organization_id,
            DeceptionSession.recommended_route == "DECEPTION",
            DeceptionSession.is_deleted == False
        ).all()
        total_trapped = len(trapped_sessions)
        
        # Journey Construction
        recent_actions = db.query(DeceptionAction).order_by(DeceptionAction.timestamp.desc()).limit(15).all()
        timeline = []
        honey_token_count = 0
        for action in recent_actions:
            if action.action_type == "HONEY_TOKEN_TRIGGERED":
                honey_token_count += 1
            timeline.append({
                "time": action.timestamp.isoformat(),
                "action": action.action_type,
                "endpoint": action.endpoint,
                "payload": action.payload,
                "session_id": action.session_id
            })

        # Phase 3 Metrics
        from ...models import FileUploadAttempt
        upload_count = db.query(FileUploadAttempt).count()
        recent_uploads = db.query(FileUploadAttempt).order_by(FileUploadAttempt.timestamp.desc()).limit(5).all()
        
        # Personas
        profiles = db.query(AttackerProfile).filter(
            AttackerProfile.organization_id == user.organization_id,
            AttackerProfile.is_deleted == False
        ).all()
        persona_counts = {}
        for p in profiles:
            persona_counts[p.persona] = persona_counts.get(p.persona, 0) + 1

        # Get notification config metrics
        from ...models import NotificationConfig
        email_sent = 0
        telegram_sent = 0
        failed_deliveries = 0
        last_email_sent = "Never"
        last_telegram_sent = "Never"
        
        config = db.query(NotificationConfig).filter(
            NotificationConfig.organization_id == user.organization_id
        ).first()
        
        if config:
            email_sent = config.email_alerts_sent or 0
            telegram_sent = config.telegram_alerts_sent or 0
            failed_deliveries = config.failed_deliveries or 0
            if config.last_email_sent_at:
                last_email_sent = config.last_email_sent_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            if config.last_telegram_sent_at:
                last_telegram_sent = config.last_telegram_sent_at.strftime("%Y-%m-%d %H:%M:%S UTC")

        result = {
            'total_events': len(events),
            'unique_ips': unique_ips,
            'avg_ml_confidence': avg_ml,
            'active_services_count': active_services,
            'events_by_service': service_counts,
            'events_by_severity': severity_counts,
            'ai_labels': label_counts,
            'hourly_trend': {
                'labels': hourly_labels,
                'data': hourly_data
            },
            'active_sessions': active_sessions,
            'high_risk_sessions': high_risk_sessions,
            'total_attacker_profiles': total_profiles,
            'total_trapped_attackers': total_trapped,
            'attacker_journey': timeline,
            'personas': persona_counts,
            'honey_token_triggers': honey_token_count,
            'file_uploads': upload_count,
            'recent_uploads': [
                {"name": u.filename, "size": u.size, "ip": u.attacker_ip} for u in recent_uploads
            ],
            'email_alerts_sent': email_sent,
            'telegram_alerts_sent': telegram_sent,
            'failed_deliveries': failed_deliveries,
            'last_email_sent_at': last_email_sent,
            'last_telegram_sent_at': last_telegram_sent,
            'last_updated': datetime.now().isoformat()
        }

        # Cache for 10 seconds
        cache_set_json(cache_key, result, ttl_seconds=10)
        return result

    except Exception as e:
        logger.warning(f"DB stats failed ({e}), using in-memory")
        return {
            'total_events': len(attack_events),
            'unique_ips': 0,
            'avg_ml_confidence': 0,
            'active_services_count': 0,
            'events_by_service': {},
            'events_by_severity': {},
            'ai_labels': {},
            'hourly_trend': {'labels': [], 'data': []},
            'active_sessions': 0,
            'high_risk_sessions': 0,
            'total_attacker_profiles': 0,
            'email_alerts_sent': 0,
            'telegram_alerts_sent': 0,
            'failed_deliveries': 0,
            'last_email_sent_at': "Never",
            'last_telegram_sent_at': "Never",
            'last_updated': datetime.now().isoformat()
        }


@router.post("/simulate-attacks")
async def simulate_attacks(
    request: Request,
    count: int = 30,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger attack simulation"""
    global_origins = [
        {"ip": "198.51.100.42", "lat": 37.0902, "lng": -95.7129, "country": "United States", "country_code": "US", "city": "Coffeyville", "region": "Kansas", "isp": "Google LLC", "flag": "🇺🇸"},
        {"ip": "95.163.220.12", "lat": 55.7558, "lng": 37.6173, "country": "Russia", "country_code": "RU", "city": "Moscow", "region": "Moscow", "isp": "Digital Ocean", "flag": "🇷🇺"},
        {"ip": "220.181.38.148", "lat": 39.9042, "lng": 116.4074, "country": "China", "country_code": "CN", "city": "Beijing", "region": "Beijing", "isp": "CHINANET", "flag": "🇨🇳"},
        {"ip": "46.165.2.14", "lat": 52.5200, "lng": 13.4050, "country": "Germany", "country_code": "DE", "city": "Berlin", "region": "Berlin", "isp": "Leaseweb", "flag": "🇩🇪"}
    ]

    new_attacks = []
    attack_types = [
        ('root', 'CRITICAL', 'malicious', 0.95, 'rm -rf /', 'SSH'),
        ('admin', 'CRITICAL', 'malicious', 0.93, 'cat /etc/shadow', 'SSH'),
        ('admin', 'HIGH', 'malicious', 0.85, 'sudo su', 'SSH'),
        ('root', 'HIGH', 'anomaly', 0.82, 'netstat -tulpn', 'HTTP'),
        ('user', 'MEDIUM', 'anomaly', 0.65, 'ls -la /root', 'SSH'),
        ('guest', 'MEDIUM', 'anomaly', 0.63, 'whoami', 'HTTP'),
        ('anonymous', 'LOW', 'benign', 0.35, 'help', 'SSH'),
        ('visitor', 'LOW', 'benign', 0.30, 'ls', 'HTTP'),
    ]

    from ...models import AttackEvent, Organization

    org = None
    try:
        org = db.query(Organization).first()
    except Exception:
        pass

    for i in range(count):
        attack = random.choice(attack_types)
        origin = random.choice(global_origins)
        
        lat_offset = random.uniform(-1.5, 1.5)
        lng_offset = random.uniform(-1.5, 1.5)
        
        simulated_ip = origin["ip"]
        parts = simulated_ip.split('.')
        if len(parts) == 4:
            simulated_ip = f"{parts[0]}.{parts[1]}.{parts[2]}.{random.randint(2, 254)}"

        new_event = {
            'id': len(attack_events) + 1,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'service': attack[5],
            'source_ip': simulated_ip,
            'source_port': random.randint(1024, 65535),
            'username': attack[0],
            'password': f"pass{random.randint(1000,9999)}",
            'command': attack[4],
            'severity': attack[1],
            'ai_label': attack[2],
            'threat_score': attack[3],
            'ml_confidence': random.uniform(0.7, 0.99) if attack[2] != 'benign' else random.uniform(0.1, 0.4),
            'location': {
                'city': origin['city'],
                'country': origin['country'],
                'country_code': origin['country_code'],
                'flag': origin['flag'],
                'isp': origin['isp'],
                'region': origin['region'],
                'lat': origin['lat'] + lat_offset,
                'lng': origin['lng'] + lng_offset,
            }
        }
        
        # Save to DB
        if db:
            try:
                db_event = AttackEvent(
                    organization_id=org.id if org else 1,
                    service_name=new_event["service"],
                    source_ip=new_event["source_ip"],
                    source_port=new_event["source_port"],
                    username=new_event["username"],
                    password=new_event["password"],
                    command=new_event["command"],
                    severity=new_event["severity"],
                    ai_label=new_event["ai_label"],
                    threat_score=new_event["threat_score"],
                    location=new_event["location"],
                    event_metadata={}
                )
                db.add(db_event)
                db.commit()
                db.refresh(db_event)
                new_event["id"] = db_event.id
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to save simulated attack to DB: {e}")

        attack_events.append(new_event)
        new_attacks.append(new_event)
        broadcaster.broadcast(new_event)

    try:
        from ...core.cache import cache_delete
        cache_delete(f"stats:{current_user['username']}")
    except Exception:
        pass

    breakdown = {sev: len([a for a in new_attacks if a['severity'] == sev]) for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]}

    return {
        "status": "success",
        "message": f"Generated {count} attacks across global origins",
        "total_attacks": len(attack_events),
        "new_attacks": len(new_attacks),
        "breakdown": breakdown
    }
