from typing import List, Tuple
from ..models import AttackerProfile, DeceptionAction
import logging

logger = logging.getLogger(__name__)

class PersonaEngine:
    """
    Analyzes attacker behavior across their history and active sessions to 
    dynamically assign a persona and calculate a confidence score.
    """
    
    PERSONAS = {
        "Scanner": "Broad exploration, low interaction, primarily automated tool paths.",
        "Credential Hunter": "Focused on authentication endpoints, repeatedly submitting login forms.",
        "Data Thief": "Attempts to access exports, download files, or interacts with Honey Tokens.",
        "Script Kiddie": "Generic payload spray, known exploit paths.",
        "Bot": "Very high frequency, zero dwell time, static signatures."
    }

    @staticmethod
    def classify_persona(profile: AttackerProfile, actions: List[DeceptionAction]) -> Tuple[str, float, str]:
        if not actions:
            return "Scanner", 0.5, "Insufficient data for advanced profiling."

        action_types = [a.action_type for a in actions]
        
        # 1. Data Thief (Highest Priority)
        data_thief_markers = ["EXPORT_DATA", "VIEW_ENV_LEAK", "HONEY_TOKEN_TRIGGERED", "FILE_DOWNLOAD"]
        data_thief_count = sum(1 for a in action_types if a in data_thief_markers)
        if data_thief_count > 0:
            confidence = min(0.6 + (data_thief_count * 0.1), 0.99)
            summary = f"High intent on data exfiltration. Triggered {data_thief_count} sensitive data traps."
            return "Data Thief", confidence, summary

        # 2. Persistence / Upload Trap
        if "FILE_UPLOAD_ATTEMPT" in action_types:
            return "Persistence Seeker", 0.85, "Attempted to upload executable payload to honeypot."

        # 3. Credential Hunter
        auth_markers = ["AUTH_FAILURE", "WP_AUTH_ATTEMPT", "DB_AUTH_ATTEMPT", "CREDENTIAL_STUFFING", "ACCOUNT_ENUMERATION"]
        auth_count = sum(1 for a in action_types if a in auth_markers)
        if auth_count > 1:
            confidence = min(0.6 + (auth_count * 0.05), 0.95)
            summary = f"Targeting authentication bypass. Captured {auth_count} login attempts."
            return "Credential Hunter", confidence, summary

        # 4. Scanner (Default)
        summary = f"Automated or manual scanning behavior. Completed {len(actions)} surface interactions."
        confidence = min(0.4 + (len(actions) * 0.05), 0.8)
        return "Scanner", confidence, summary

    @staticmethod
    def update_profile_persona(profile: AttackerProfile, actions: List[DeceptionAction]):
        persona, confidence, summary = PersonaEngine.classify_persona(profile, actions)
        
        # Only upgrade confidence or escalate persona severity
        # (Data Thief > Credential Hunter > Scanner)
        hierarchy = {"Data Thief": 4, "Persistence Seeker": 3, "Credential Hunter": 2, "Scanner": 1, "Bot": 1}
        
        current_rank = hierarchy.get(profile.persona, 0)
        new_rank = hierarchy.get(persona, 0)
        
        if new_rank >= current_rank or confidence > (profile.confidence_score or 0.0):
            profile.persona = persona
            profile.confidence_score = confidence
            profile.behavior_summary = summary
