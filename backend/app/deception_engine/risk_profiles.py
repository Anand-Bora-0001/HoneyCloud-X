# backend/app/deception_engine/risk_profiles.py

class RiskProfileManager:
    """
    Determines risk levels based on dynamic thresholds.
    """
    
    THRESHOLDS = {
        "LOW": 0.0,
        "MEDIUM": 40.0,
        "HIGH": 70.0,
        "CRITICAL": 90.0
    }

    @classmethod
    def calculate_risk_level(cls, threat_score: float) -> str:
        if threat_score >= cls.THRESHOLDS["CRITICAL"]:
            return "CRITICAL"
        if threat_score >= cls.THRESHOLDS["HIGH"]:
            return "HIGH"
        if threat_score >= cls.THRESHOLDS["MEDIUM"]:
            return "MEDIUM"
        return "LOW"
        
    @classmethod
    def get_action_score(cls, action_type: str, payload: str) -> float:
        """
        Calculate baseline score delta for a given action.
        """
        base_scores = {
            "VISIT": 1.0,
            "SCAN": 5.0,
            "DIRECTORY_SCAN": 10.0,
            "ACCOUNT_ENUMERATION": 12.0,
            "AUTH_FAILURE": 15.0,
            "CREDENTIAL_STUFFING": 20.0,
            "SQLI_ATTEMPT": 25.0,
            "XSS_ATTEMPT": 20.0,
            "COMMAND_INJECTION": 30.0,
            "ADMIN_ENUMERATION": 15.0
        }
        
        score = base_scores.get(action_type, 2.0)
        
        # Payload complexity modifier
        if payload and len(payload) > 50:
            score += 5.0
        if payload and ("%00" in payload or "../" in payload):
            score += 10.0
            
        return score
