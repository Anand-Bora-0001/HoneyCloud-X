from typing import List, Dict, Any
from datetime import datetime

class TimelineAnalyzer:
    """Reconstructs the attack timeline, paths, and dwell time."""

    @staticmethod
    def analyze_actions(actions: List[Any]) -> Dict[str, Any]:
        if not actions:
            return {"attack_paths": [], "dwell_time_seconds": 0}

        actions_sorted = sorted(actions, key=lambda a: a.timestamp)
        paths = []
        
        # Build Attack Path Transitions
        for i in range(len(actions_sorted)):
            action = actions_sorted[i]
            # Simple path node representation
            paths.append({
                "from": actions_sorted[i-1].endpoint if i > 0 else "External",
                "to": action.endpoint or action.action_type,
                "action": action.action_type,
                "time": action.timestamp.isoformat() if action.timestamp else None,
                "payload": action.payload
            })
            
        start_time = actions_sorted[0].timestamp
        end_time = actions_sorted[-1].timestamp
        
        dwell_time = 0
        if start_time and end_time:
            dwell_time = int((end_time - start_time).total_seconds())

        return {
            "attack_paths": paths,
            "dwell_time_seconds": dwell_time,
            "total_nodes": len(paths)
        }
