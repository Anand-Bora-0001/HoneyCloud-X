from typing import Dict, Any

class ProfileBuilder:
    """Generates human-readable narratives based on evidence and calculates risk trends."""
    
    @staticmethod
    def generate_narrative(evidence: Dict[str, Any]) -> str:
        narrative = []
        
        # Opening
        if evidence["total_sessions"] > 1:
            narrative.append(f"This attacker returned {evidence['total_sessions']} times, indicating persistent interest.")
        else:
            narrative.append("This attacker executed a single, potentially automated hit-and-run session.")
            
        # Behavior Profile
        persona = evidence["persona"]
        if persona == "Scanner":
            narrative.append("Their behavior primarily consisted of surface-level reconnaissance and vulnerability scanning.")
        elif persona == "Credential Hunter":
            narrative.append(f"The attacker focused heavily on authentication bypass, submitting {evidence['login_attempts']} brute-force attempts.")
        elif persona == "Persistence Seeker":
            narrative.append(f"The attacker attempted to establish persistence by uploading {evidence['upload_attempts']} files (likely web shells or malware) into the honeypot.")
        elif persona == "Data Thief":
            narrative.append(f"The attacker demonstrated clear data exfiltration intent, attempting {evidence['exports_attempted']} data exports and triggering {evidence['honey_tokens_triggered']} honey tokens.")
            
        # Specifics
        if evidence["most_targeted_endpoint"] != "None":
            narrative.append(f"Their primary target of interest was '{evidence['most_targeted_endpoint']}'.")
            
        # Conclusion
        confidence = int(evidence["confidence"] * 100)
        narrative.append(f"\nClassification: {persona} (Confidence: {confidence}%).")
        
        return " ".join(narrative)
        
    @staticmethod
    def calculate_risk_trend(sessions: list) -> Dict[str, Any]:
        if not sessions or len(sessions) < 2:
            return {"trend": "Stable", "message": "Insufficient session history to calculate a trend."}
            
        # Sort sessions by time
        sessions_sorted = sorted(sessions, key=lambda s: s.started_at)
        first_score = sessions_sorted[0].threat_score
        last_score = sessions_sorted[-1].threat_score
        
        if last_score > first_score + 10:
            trend = "Escalating"
        elif last_score < first_score - 10:
            trend = "De-escalating"
        else:
            trend = "Stable"
            
        return {
            "trend": trend,
            "first_score": first_score,
            "last_score": last_score,
            "message": f"Threat score moved from {first_score:.1f} to {last_score:.1f}."
        }
