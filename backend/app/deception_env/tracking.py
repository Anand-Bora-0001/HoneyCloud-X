
from fastapi import Request
from ..database import SessionLocal
from ..models import DeceptionAction
import logging

logger = logging.getLogger(__name__)

def track_deception_action(request: Request, action_type: str, endpoint: str, payload: str = ""):
    session_id = request.query_params.get("sid") or request.cookies.get("deception_session_id")
    if not session_id:
        logger.warning("No session ID found for tracking deception action.")
        return
    db = SessionLocal()
    try:
        action = DeceptionAction(
            session_id=session_id,
            action_type=action_type,
            endpoint=endpoint,
            method=request.method,
            payload=payload,
            threat_score=0.0 # Just tracking, not escalating inside the trap
        )
        db.add(action)
        db.commit()
    except Exception as e:
        logger.error(f"Tracking error: {e}")
    finally:
        db.close()
