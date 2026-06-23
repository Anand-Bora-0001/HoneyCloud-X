from typing import List, Any, Dict

class EvidenceCollector:
    """Aggregates raw data into structured evidence for the narrative generator."""
    
    @staticmethod
    def collect(profile: Any, sessions: List[Any], actions: List[Any], uploads: List[Any]) -> Dict[str, Any]:
        honey_tokens_triggered = sum(1 for a in actions if a.action_type == "HONEY_TOKEN_TRIGGERED")
        exports_attempted = sum(1 for a in actions if a.action_type == "EXPORT_DATA")
        login_attempts = sum(1 for a in actions if "AUTH_ATTEMPT" in a.action_type or a.action_type == "AUTH_FAILURE")
        
        # Determine most targeted endpoint
        endpoints = [a.endpoint for a in actions if a.endpoint]
        most_targeted = max(set(endpoints), key=endpoints.count) if endpoints else "None"
        
        # Map uploads
        upload_metadata = [{"filename": u.filename, "hash": u.file_hash, "size": u.size} for u in uploads]

        return {
            "total_sessions": len(sessions),
            "total_actions": len(actions),
            "honey_tokens_triggered": honey_tokens_triggered,
            "exports_attempted": exports_attempted,
            "login_attempts": login_attempts,
            "most_targeted_endpoint": most_targeted,
            "upload_attempts": len(uploads),
            "upload_metadata": upload_metadata,
            "threat_score_avg": profile.average_threat_score,
            "persona": profile.persona,
            "confidence": profile.confidence_score
        }
