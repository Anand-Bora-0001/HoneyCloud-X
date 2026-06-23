from sqlalchemy.orm import Session
from ..models import AttackerProfile, DeceptionSession, DeceptionAction, FileUploadAttempt, InvestigationReport
from .evidence_collector import EvidenceCollector
from .timeline_analyzer import TimelineAnalyzer
from .profile_builder import ProfileBuilder
from .mitre_mapper import MitreMapper
from .correlation_engine import CorrelationEngine
import logging

logger = logging.getLogger(__name__)

class InvestigationService:
    """Orchestrates the creation and updating of full attacker investigations."""
    
    @staticmethod
    def run_investigation(db: Session, profile_id: int):
        try:
            profile = db.query(AttackerProfile).filter(AttackerProfile.id == profile_id).first()
            if not profile:
                return None
                
            # Fetch all associated data
            sessions = db.query(DeceptionSession).filter(DeceptionSession.source_ip == profile.source_ip).all()
            session_ids = [s.session_id for s in sessions]
            
            actions = []
            uploads = []
            if session_ids:
                actions = db.query(DeceptionAction).filter(DeceptionAction.session_id.in_(session_ids)).all()
                uploads = db.query(FileUploadAttempt).filter(FileUploadAttempt.session_id.in_(session_ids)).all()
                
            # 1. Collect Evidence
            evidence = EvidenceCollector.collect(profile, sessions, actions, uploads)
            
            # 2. Reconstruct Timeline
            timeline = TimelineAnalyzer.analyze_actions(actions)
            
            # 3. MITRE Mapping
            mitre_map = MitreMapper.map_actions([a.action_type for a in actions])
            
            # 4. Generate Narrative & Trends
            narrative = ProfileBuilder.generate_narrative(evidence)
            risk_trend = ProfileBuilder.calculate_risk_trend(sessions)
            
            # 5. Build/Update Report
            report = db.query(InvestigationReport).filter(InvestigationReport.attacker_profile_id == profile.id).first()
            if not report:
                report = InvestigationReport(
                    attacker_profile_id=profile.id,
                    organization_id=profile.organization_id
                )
                db.add(report)
                
            report.summary_narrative = narrative
            report.executive_summary = f"Profile {profile.source_ip} is classified as {profile.persona} with {profile.confidence_score * 100:.0f}% confidence."
            report.technical_summary = f"Triggered {len(mitre_map)} distinct MITRE ATT&CK techniques. Attack path spans {timeline['total_nodes']} nodes over {timeline['dwell_time_seconds']} seconds."
            report.mitre_mapping = mitre_map
            report.attack_paths = timeline["attack_paths"]
            report.risk_evolution_trend = risk_trend
            report.evidence_summary = evidence
            
            db.commit()
            db.refresh(report)
            
            # 6. Run Correlation
            CorrelationEngine.correlate_profile(db, profile)
            
            return report
            
        except Exception as e:
            logger.error(f"Investigation failed for profile {profile_id}: {e}")
            db.rollback()
            return None
