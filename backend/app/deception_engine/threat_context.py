# backend/app/deception_engine/threat_context.py
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class ThreatContext:
    """
    Represents the context of an ongoing attack session.
    """
    def __init__(
        self,
        session_id: str,
        source_ip: str,
        user_agent: str,
        organization_id: int,
        service_id: Optional[int] = None
    ):
        self.session_id = session_id
        self.source_ip = source_ip
        self.user_agent = user_agent
        self.organization_id = organization_id
        self.service_id = service_id
        
        self.started_at = datetime.now(timezone.utc)
        self.last_seen = self.started_at
        
        self.action_history = []
        self.threat_score = 0.0
        self.risk_level = "LOW"
        
        self.metrics = {
            "total_requests": 0,
            "unique_endpoints": set(),
            "payload_complexity": 0.0,
            "failed_auths": 0
        }

    def add_action(self, endpoint: str, method: str, payload: str, action_type: str, score_delta: float):
        self.last_seen = datetime.now(timezone.utc)
        self.action_history.append({
            "endpoint": endpoint,
            "method": method,
            "payload": payload,
            "action_type": action_type,
            "timestamp": self.last_seen
        })
        
        self.metrics["total_requests"] += 1
        if endpoint:
            self.metrics["unique_endpoints"].add(endpoint)
        if action_type == "AUTH_FAILURE":
            self.metrics["failed_auths"] += 1
            
        self.threat_score = min(100.0, self.threat_score + score_delta)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "source_ip": self.source_ip,
            "threat_score": self.threat_score,
            "risk_level": self.risk_level,
            "total_requests": self.metrics["total_requests"],
            "unique_endpoints_count": len(self.metrics["unique_endpoints"])
        }
