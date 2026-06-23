from sqlalchemy.orm import Session
from ..models import AttackerProfile, ThreatCampaign, DeceptionAction
import logging

logger = logging.getLogger(__name__)

class CorrelationEngine:
    """Correlates multiple attacker profiles into unified Threat Campaigns based on shared indicators."""
    
    @staticmethod
    def correlate_profile(db: Session, profile: AttackerProfile):
        try:
            # Simple heuristic: Group by Subnet (/24) AND Persona
            ip_parts = profile.source_ip.split('.')
            if len(ip_parts) != 4:
                return # Skip IPv6 for this basic heuristic
                
            subnet = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
            campaign_name = f"{profile.persona} Activity from {subnet}"
            
            campaign = db.query(ThreatCampaign).filter(
                ThreatCampaign.organization_id == profile.organization_id,
                ThreatCampaign.name == campaign_name
            ).first()
            
            if not campaign:
                campaign = ThreatCampaign(
                    organization_id=profile.organization_id,
                    name=campaign_name,
                    description=f"Automated grouping of {profile.persona}s originating from the {subnet} subnet.",
                    confidence_score=profile.confidence_score,
                    common_personas=[profile.persona],
                    common_endpoints=list(profile.most_targeted_endpoints.keys()) if profile.most_targeted_endpoints else [],
                    common_payloads=list(profile.most_common_payloads.keys()) if profile.most_common_payloads else []
                )
                db.add(campaign)
                db.commit()
            else:
                # Update campaign confidence
                campaign.confidence_score = max(campaign.confidence_score, profile.confidence_score)
                db.commit()
                
        except Exception as e:
            logger.error(f"Failed to correlate profile {profile.id}: {e}")
            db.rollback()
