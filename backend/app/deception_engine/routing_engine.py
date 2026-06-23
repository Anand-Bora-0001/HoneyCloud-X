# backend/app/deception_engine/routing_engine.py
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from .threat_context import ThreatContext
from .decision_engine import DecisionEngine
from .risk_profiles import RiskProfileManager
from ..models import DeceptionSession, DeceptionAction, AttackerProfile

class ThreatRoutingEngine:
    """
    Main entry point for evaluating incoming requests and tracking sessions.
    """
    
    def __init__(self, db: Session):
        self.db = db

    def evaluate_request(self, 
                         source_ip: str, 
                         endpoint: str, 
                         method: str, 
                         payload: str, 
                         organization_id: int, 
                         service_id: Optional[int], 
                         user_agent: str, 
                         action_type: str = "VISIT") -> Dict[str, Any]:
        
        # 1. Profile Tracking
        profile = self._get_or_create_profile(source_ip, organization_id)
        
        # 2. Session Tracking
        session = self._get_active_session(source_ip, organization_id, service_id, user_agent)
        
        # Calculate score delta
        score_delta = RiskProfileManager.get_action_score(action_type, payload)
        
        # Update session
        session.threat_score = min(100.0, session.threat_score + score_delta)
        session.risk_level = RiskProfileManager.calculate_risk_level(session.threat_score)
        session.last_seen = datetime.now(timezone.utc)
        
        # 3. Create context for Decision Engine
        context = ThreatContext(
            session_id=session.session_id,
            source_ip=session.source_ip,
            user_agent=session.user_agent,
            organization_id=session.organization_id,
            service_id=session.service_id
        )
        context.threat_score = session.threat_score
        
        # 4. Make decision
        decision = DecisionEngine.evaluate(context)
        session.recommended_route = decision["recommended_route"]
        
        # 5. Log action
        action = DeceptionAction(
            session_id=session.session_id,
            action_type=action_type,
            endpoint=endpoint,
            method=method,
            payload=payload,
            threat_score=score_delta
        )
        self.db.add(action)
        
        # 6. Update profile
        self._update_profile(profile, session, endpoint, payload)
        
        self.db.commit()
        
        return {
            "session_id": session.session_id,
            "threat_score": session.threat_score,
            "risk_level": session.risk_level,
            "recommended_route": session.recommended_route,
            "reasoning": decision["reasoning"]
        }

    def _get_or_create_profile(self, source_ip: str, organization_id: int) -> AttackerProfile:
        profile = self.db.query(AttackerProfile).filter_by(source_ip=source_ip, organization_id=organization_id).first()
        if not profile:
            profile = AttackerProfile(source_ip=source_ip, organization_id=organization_id)
            self.db.add(profile)
            self.db.commit()
        return profile

    def _get_active_session(self, source_ip: str, organization_id: int, service_id: int, user_agent: str) -> DeceptionSession:
        # Find active session within last 1 hour
        session = self.db.query(DeceptionSession).filter(
            DeceptionSession.source_ip == source_ip,
            DeceptionSession.organization_id == organization_id,
            DeceptionSession.status == "ACTIVE"
        ).order_by(DeceptionSession.last_seen.desc()).first()
        
        if not session:
            session_id = str(uuid.uuid4())
            session = DeceptionSession(
                session_id=session_id,
                source_ip=source_ip,
                user_agent=user_agent,
                organization_id=organization_id,
                service_id=service_id
            )
            self.db.add(session)
            self.db.commit()
            
            # Update profile total sessions
            profile = self._get_or_create_profile(source_ip, organization_id)
            profile.total_sessions += 1
            self.db.commit()
            
        return session
        
    def _update_profile(self, profile: AttackerProfile, session: DeceptionSession, endpoint: str, payload: str):
        profile.total_attacks += 1
        
        # Rolling average
        if profile.total_attacks == 1:
            profile.average_threat_score = session.threat_score
        else:
            profile.average_threat_score = ((profile.average_threat_score * (profile.total_attacks - 1)) + session.threat_score) / profile.total_attacks
            
        profile.risk_category = RiskProfileManager.calculate_risk_level(profile.average_threat_score)
        
        # Update top endpoints (naive approach)
        if endpoint:
            eps = profile.most_targeted_endpoints or {}
            eps[endpoint] = eps.get(endpoint, 0) + 1
            profile.most_targeted_endpoints = eps
            
        profile.last_seen = datetime.now(timezone.utc)
