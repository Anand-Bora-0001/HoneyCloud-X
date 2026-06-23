"""
HoneyCloud-X Reporting Scheduler Service
Handles automatic daily summaries and weekly executive reports with attachments.
"""
import os
import json
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from ..database import SessionLocal, get_db
from ..models import Organization, NotificationConfig, AttackEvent, AttackerProfile, ThreatCampaign
from .email_service import email_service
from ..report_generator import generate_pdf_report, generate_csv_report
from ..deception_engine.persona_engine import PersonaEngine
from ..investigation_engine.mitre_mapper import MitreMapper

logger = logging.getLogger(__name__)

STATE_FILE = "reports/scheduler_state.json"

class ReportingScheduler:
    """Manages scheduling and generation of daily and weekly reports"""
    
    def __init__(self):
        self.state_file = STATE_FILE
        self._ensure_reports_dir()
        self.state = self._load_state()
        
    def _ensure_reports_dir(self):
        os.makedirs("reports", exist_ok=True)
        
    def _load_state(self) -> Dict[str, Any]:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load scheduler state: {e}")
        return {}
        
    def _save_state(self):
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save scheduler state: {e}")
            
    def _get_last_report_times(self, org_id: int) -> Dict[str, Any]:
        key = str(org_id)
        if key not in self.state:
            self.state[key] = {
                "last_daily_summary_at": None,
                "last_weekly_report_at": None
            }
        return self.state[key]
        
    def _update_last_report_time(self, org_id: int, report_type: str):
        key = str(org_id)
        if key not in self.state:
            self.state[key] = {}
        self.state[key][f"last_{report_type}_at"] = datetime.now(timezone.utc).isoformat()
        self._save_state()

    async def run_scheduler(self):
        """Infinite loop executing the hourly scheduler checks"""
        logger.info("📅 HoneyCloud-X Reporting Scheduler started")
        while True:
            try:
                await asyncio.sleep(3600)  # Check every hour
                await self.check_and_trigger_reports()
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                
    async def check_and_trigger_reports(self):
        """Queries configs and checks if daily or weekly thresholds have expired"""
        db = SessionLocal()
        try:
            orgs = db.query(Organization).all()
            for org in orgs:
                config = db.query(NotificationConfig).filter(
                    NotificationConfig.organization_id == org.id
                ).first()
                
                if not config or not config.email_enabled or not config.email_addresses:
                    continue
                    
                times = self._get_last_report_times(org.id)
                now = datetime.now(timezone.utc)
                
                # Daily Security Summary check
                if config.daily_summary_enabled:
                    last_daily = times.get("last_daily_summary_at")
                    should_send_daily = False
                    if not last_daily:
                        should_send_daily = True
                    else:
                        last_dt = datetime.fromisoformat(last_daily)
                        if now - last_dt >= timedelta(days=1):
                            should_send_daily = True
                            
                    if should_send_daily:
                        logger.info(f"Triggering Daily Security Summary for Org {org.name}")
                        success = await self.generate_and_send_daily_summary(db, org, config.email_addresses)
                        if success:
                            self._update_last_report_time(org.id, "daily_summary")
                            
                # Weekly Executive Report check
                if config.weekly_report_enabled:
                    last_weekly = times.get("last_weekly_report_at")
                    should_send_weekly = False
                    if not last_weekly:
                        should_send_weekly = True
                    else:
                        last_dt = datetime.fromisoformat(last_weekly)
                        if now - last_dt >= timedelta(days=7):
                            should_send_weekly = True
                            
                    if should_send_weekly:
                        logger.info(f"Triggering Weekly Executive Report for Org {org.name}")
                        success = await self.generate_and_send_weekly_report(db, org, config.email_addresses)
                        if success:
                            self._update_last_report_time(org.id, "weekly_report")
        finally:
            db.close()

    async def generate_and_send_daily_summary(self, db: Session, org: Organization, recipients: List[str]) -> bool:
        """Collects 24h stats, builds HTML daily summary, and dispatches it"""
        try:
            one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
            
            # Events in the last 24h
            events = db.query(AttackEvent).filter(
                AttackEvent.organization_id == org.id,
                AttackEvent.timestamp >= one_day_ago,
                AttackEvent.is_deleted == False
            ).all()
            
            total_attacks = len(events)
            critical_threats = sum(1 for e in events if e.severity == 'CRITICAL')
            
            # Persona distributions
            profiles = db.query(AttackerProfile).filter(
                AttackerProfile.organization_id == org.id,
                AttackerProfile.last_seen >= one_day_ago,
                AttackerProfile.is_deleted == False
            ).all()
            
            personas = {}
            for p in profiles:
                personas[p.persona] = personas.get(p.persona, 0) + 1
            top_persona = max(personas, key=personas.get) if personas else "None"
            
            # Geographic stats
            countries = {}
            for e in events:
                if e.location and isinstance(e.location, dict):
                    c = e.location.get('country')
                    if c:
                        countries[c] = countries.get(c, 0) + 1
            top_countries = sorted(countries.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Attack types (Services)
            services = {}
            for e in events:
                s = e.service_name
                if s:
                    services[s] = services.get(s, 0) + 1
            top_services = sorted(services.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # MITRE Stats
            actions = [e.command or e.endpoint or 'VISIT' for e in events]
            mitre_map = MitreMapper.map_actions(actions)
            mitre_counts = {}
            for e in events:
                act = e.command or e.endpoint or 'VISIT'
                if act in MitreMapper.MAPPING:
                    tech_id = MitreMapper.MAPPING[act]["id"]
                    mitre_counts[tech_id] = mitre_counts.get(tech_id, 0) + 1
            
            mitre_details = []
            for tech_id, name in mitre_map.items():
                count = mitre_counts.get(tech_id, 0)
                mitre_details.append({"id": tech_id, "name": name, "count": count})
                
            # Render Daily Summary HTML Body
            html_body = self._build_daily_html(
                org.name, total_attacks, critical_threats, top_persona, top_countries, top_services, mitre_details
            )
            
            subject = f"📊 HoneyCloud-X Daily Security Report - {org.name}"
            
            # Send email asynchronously
            return await email_service.send_email(
                to_emails=recipients,
                subject=subject,
                html_body=html_body,
                text_body=f"HoneyCloud-X Daily Report: {total_attacks} attacks, {critical_threats} critical threats."
            )
        except Exception as e:
            logger.error(f"Failed to generate Daily Security Summary: {e}")
            return False

    async def generate_and_send_weekly_report(self, db: Session, org: Organization, recipients: List[str]) -> bool:
        """Collects 7d stats, creates CSV & PDF reports, builds weekly summary, and sends with attachments"""
        try:
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            
            # Events in the last 7 days
            events_db = db.query(AttackEvent).filter(
                AttackEvent.organization_id == org.id,
                AttackEvent.timestamp >= seven_days_ago,
                AttackEvent.is_deleted == False
            ).all()
            
            events = []
            service_counts = {}
            severity_counts = {}
            ai_labels = {}
            
            for e in events_db:
                evt_dict = {
                    "id": e.id,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                    "service": e.service_name,
                    "source_ip": e.source_ip,
                    "severity": e.severity,
                    "ai_label": e.ai_label,
                    "threat_score": e.threat_score or 0.0,
                    "command": e.command
                }
                events.append(evt_dict)
                
                # Accrue stats
                s = e.service_name or 'UNKNOWN'
                service_counts[s] = service_counts.get(s, 0) + 1
                sv = e.severity or 'UNKNOWN'
                severity_counts[sv] = severity_counts.get(sv, 0) + 1
                lbl = e.ai_label or 'unknown'
                ai_labels[lbl] = ai_labels.get(lbl, 0) + 1
                
            stats = {
                "total_events": len(events),
                "events_by_service": service_counts,
                "events_by_severity": severity_counts,
                "ai_labels": ai_labels
            }
            
            # Query active campaigns
            campaigns = db.query(ThreatCampaign).filter(
                ThreatCampaign.organization_id == org.id,
                ThreatCampaign.created_at >= seven_days_ago
            ).all()
            
            # Calculate growth trends (last week vs week before)
            forteen_days_ago = datetime.now(timezone.utc) - timedelta(days=14)
            prev_week_events = db.query(AttackEvent).filter(
                AttackEvent.organization_id == org.id,
                AttackEvent.timestamp >= forteen_days_ago,
                AttackEvent.timestamp < seven_days_ago,
                AttackEvent.is_deleted == False
            ).count()
            
            current_week_count = len(events)
            growth_rate = 0.0
            if prev_week_events > 0:
                growth_rate = ((current_week_count - prev_week_events) / prev_week_events) * 100
                
            # Create attachments
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            pdf_path = f"reports/weekly_report_{org.id}_{timestamp_str}.pdf"
            csv_path = f"reports/weekly_report_{org.id}_{timestamp_str}.csv"
            
            generate_pdf_report(events, stats, pdf_path)
            generate_csv_report(events, csv_path)
            
            # Check if PDF exists (it could have generated a .txt fallback)
            attachments = []
            if os.path.exists(pdf_path):
                attachments.append(pdf_path)
            elif os.path.exists(pdf_path.replace('.pdf', '.txt')):
                attachments.append(pdf_path.replace('.pdf', '.txt'))
                
            if os.path.exists(csv_path):
                attachments.append(csv_path)
                
            # Generate Weekly HTML body
            html_body = self._build_weekly_html(
                org.name, current_week_count, prev_week_events, growth_rate, campaigns, severity_counts
            )
            
            subject = f"📊 HoneyCloud-X Weekly Executive Report - {org.name}"
            
            # Send Email
            success = await email_service.send_email(
                to_emails=recipients,
                subject=subject,
                html_body=html_body,
                text_body=f"HoneyCloud-X Weekly Report: {current_week_count} attacks, growth trend {growth_rate:.1f}%. Attachments attached.",
                attachments=attachments
            )
            
            # Clean up attachments from disk after dispatch to save space
            for path in attachments:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception as clean_err:
                    logger.warning(f"Could not clean up report attachment: {clean_err}")
                    
            return success
            
        except Exception as e:
            logger.error(f"Failed to generate Weekly Executive Report: {e}")
            return False

    def _build_daily_html(
        self, org_name: str, total_attacks: int, critical: int, top_persona: str,
        top_countries: list, top_services: list, mitre_stats: list
    ) -> str:
        # Build country rows HTML
        country_rows = ""
        for country, count in top_countries:
            country_rows += f"<tr><td style='padding: 8px 0; color:#e2e8f0;'>{country}</td><td style='padding: 8px 0; text-align:right; font-weight:bold; color:#38bdf8;'>{count}</td></tr>"
        if not country_rows:
            country_rows = "<tr><td colspan='2' style='padding: 8px 0; text-align:center; color:#94a3b8;'>No geographic data recorded</td></tr>"
            
        # Build service rows HTML
        service_rows = ""
        for service, count in top_services:
            service_rows += f"<tr><td style='padding: 8px 0; color:#e2e8f0;'>{service}</td><td style='padding: 8px 0; text-align:right; font-weight:bold; color:#38bdf8;'>{count}</td></tr>"
        if not service_rows:
            service_rows = "<tr><td colspan='2' style='padding: 8px 0; text-align:center; color:#94a3b8;'>No service telemetry logged</td></tr>"

        # Build mitre rows HTML
        mitre_rows = ""
        for item in mitre_stats:
            mitre_rows += f"<tr><td style='padding: 8px 0; font-family:monospace; color:#fb7185;'>{item['id']}</td><td style='padding: 8px 0; color:#e2e8f0;'>{item['name']}</td><td style='padding: 8px 0; text-align:right; font-weight:bold; color:#38bdf8;'>{item['count']}</td></tr>"
        if not mitre_rows:
            mitre_rows = "<tr><td colspan='3' style='padding: 8px 0; text-align:center; color:#94a3b8;'>No MITRE techniques triggered</td></tr>"

        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #0f172a; color: #1e293b; padding: 20px; margin: 0;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.05); overflow: hidden; padding: 24px; color: #f8fafc;">
                
                <div style="border-bottom: 2px solid #38bdf8; padding-bottom: 12px; margin-bottom: 20px; text-align:center;">
                    <h1 style="margin: 0; color: #38bdf8; font-size: 24px;">📊 HoneyCloud-X Daily Security Report</h1>
                    <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 13px; text-transform:uppercase;">Organization: {org_name}</p>
                </div>
                
                <h3 style="color:#38bdf8; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom:4px; margin-top:0;">🛡️ Executive Summary</h3>
                <p style="color:#cbd5e1; font-size:14px; line-height:1.5;">
                    Over the last 24 hours, HoneyCloud-X monitored active endpoints for potential incursion activities. A total of <strong>{total_attacks}</strong> threat vectors were identified and contained. Of these, <strong>{critical}</strong> events were classified as Critical severity, requiring immediate attention. The dominant actor profile was classified as <strong>{top_persona}</strong>.
                </p>
                
                <div style="margin-top: 20px;">
                    <h3 style="color:#38bdf8; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom:4px;">🎯 Targeted Decoy Services</h3>
                    <table style="width:100%; border-collapse:collapse; font-size:13px;">
                        {service_rows}
                    </table>
                </div>

                <div style="margin-top: 20px;">
                    <h3 style="color:#38bdf8; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom:4px;">🌍 Attacker Origin Geographies (Top 5)</h3>
                    <table style="width:100%; border-collapse:collapse; font-size:13px;">
                        {country_rows}
                    </table>
                </div>
                
                <div style="margin-top: 20px;">
                    <h3 style="color:#38bdf8; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom:4px;">🛡️ MITRE ATT&CK Alignment</h3>
                    <table style="width:100%; border-collapse:collapse; font-size:13px;">
                        <thead>
                            <tr style="text-align:left; color:#94a3b8;">
                                <th style="padding-bottom: 8px;">ID</th>
                                <th style="padding-bottom: 8px;">Technique Name</th>
                                <th style="padding-bottom: 8px; text-align:right;">Count</th>
                            </tr>
                        </thead>
                        <tbody>
                            {mitre_rows}
                        </tbody>
                    </table>
                </div>

                <div style="margin-top: 30px; text-align: center; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 15px; font-size: 11px; color: #64748b;">
                    <p style="margin: 0;">This report is generated dynamically by HoneyCloud-X SOC Scheduler.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def _build_weekly_html(
        self, org_name: str, total_attacks: int, prev_attacks: int, growth_rate: float,
        campaigns: list, severity_counts: dict
    ) -> str:
        # Format growth trend text
        growth_text = f"+{growth_rate:.1f}% increase from last week" if growth_rate > 0 else f"{growth_rate:.1f}% decrease from last week"
        growth_color = "#ef4444" if growth_rate > 0 else "#22c55e"
        
        # Build campaign HTML
        campaign_list_html = ""
        for c in campaigns:
            campaign_list_html += f"<li style='margin-bottom:8px; color:#e2e8f0;'><strong>{c.name}</strong> - Confidence: {c.confidence_score*100:.0f}%<br><span style='font-size:12px; color:#94a3b8;'>{c.description or 'No details available.'}</span></li>"
        if not campaign_list_html:
            campaign_list_html = "<li style='color:#94a3b8;'>No coordinated threat campaigns detected this week.</li>"

        # Severity distributions
        critical = severity_counts.get("CRITICAL", 0)
        high = severity_counts.get("HIGH", 0)
        medium = severity_counts.get("MEDIUM", 0)
        low = severity_counts.get("LOW", 0)

        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #0f172a; color: #1e293b; padding: 20px; margin: 0;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.05); overflow: hidden; padding: 24px; color: #f8fafc;">
                
                <div style="border-bottom: 2px solid #a855f7; padding-bottom: 12px; margin-bottom: 20px; text-align:center;">
                    <h1 style="margin: 0; color: #a855f7; font-size: 24px;">📊 HoneyCloud-X Weekly Executive Report</h1>
                    <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 13px; text-transform:uppercase;">Organization: {org_name}</p>
                </div>
                
                <h3 style="color:#a855f7; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom:4px; margin-top:0;">🛡️ Executive Summary</h3>
                <p style="color:#cbd5e1; font-size:14px; line-height:1.5;">
                    We are pleased to deliver this weekly intelligence brief from HoneyCloud-X. Over the last 7 days, HoneyCloud-X monitored decoy sensors and logged <strong>{total_attacks}</strong> total threat attempts.
                    Compare to the previous week ({prev_attacks} attempts), this represents a <strong style="color: {growth_color};">{growth_text}</strong>.
                </p>
                
                <div style="margin-top: 20px; background-color:rgba(0,0,0,0.15); padding:16px; border-radius:6px; border:1px solid rgba(255,255,255,0.03);">
                    <h4 style="margin:0 0 8px 0; color:#cbd5e1;">Severity Breakdown</h4>
                    <table style="width:100%; font-size:13px; border-collapse:collapse;">
                        <tr><td style="padding:4px 0; color:#ef4444; font-weight:bold;">Critical Severity:</td><td style="padding:4px 0; text-align:right; font-weight:bold; color:#ef4444;">{critical}</td></tr>
                        <tr><td style="padding:4px 0; color:#f97316;">High Severity:</td><td style="padding:4px 0; text-align:right; font-weight:bold; color:#f97316;">{high}</td></tr>
                        <tr><td style="padding:4px 0; color:#38bdf8;">Medium Severity:</td><td style="padding:4px 0; text-align:right; font-weight:bold; color:#38bdf8;">{medium}</td></tr>
                        <tr><td style="padding:4px 0; color:#84cc16;">Low Severity:</td><td style="padding:4px 0; text-align:right; font-weight:bold; color:#84cc16;">{low}</td></tr>
                    </table>
                </div>

                <div style="margin-top: 20px;">
                    <h3 style="color:#a855f7; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom:4px;">🔍 Coordinated Threat Campaigns</h3>
                    <ul style="padding-left:20px; margin:0;">
                        {campaign_list_html}
                    </ul>
                </div>

                <div style="margin-top: 20px; background-color: rgba(168, 85, 247, 0.03); border-left: 4px solid #a855f7; padding: 15px; border-radius: 0 8px 8px 0;">
                    <h4 style="margin: 0 0 8px 0; color: #f8fafc; font-size: 14px; font-weight: 600;">📋 SOC Recommendations</h4>
                    <ul style="margin: 0; padding-left: 20px; color: #cbd5e1; font-size: 13px; line-height: 1.4;">
                        <li style="margin-bottom: 5px;">Examine raw telemetry spreadsheet attached to this email.</li>
                        <li style="margin-bottom: 5px;">Investigate any active threat campaigns to review source networks.</li>
                        <li>Consider blacklisting persistent subnets targeting decoy services.</li>
                    </ul>
                </div>

                <div style="margin-top: 30px; text-align: center; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 15px; font-size: 11px; color: #64748b;">
                    <p style="margin: 0;">This weekly brief was automatically exported and emailed. PDF & CSV files are attached.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

# Global scheduler instance
reporting_scheduler = ReportingScheduler()

def start_reporting_scheduler():
    """Start background scheduler loop task"""
    try:
        asyncio.create_task(reporting_scheduler.run_scheduler())
        logger.info("✅ Background reporting scheduler task started")
    except Exception as e:
        logger.error(f"Failed to start background scheduler: {e}")
