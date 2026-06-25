import re
from typing import Optional
from ..database import SessionLocal
from ..models import DeceptionScenario
import logging

logger = logging.getLogger(__name__)

def evaluate_scenario(endpoint: str, payload: str = "") -> Optional[str]:
    """
    Evaluates an attack payload/endpoint against active scenarios to
    determine the best deception environment redirect url.
    """
    db = SessionLocal()
    try:
        # Load active scenarios ordered by priority
        scenarios = db.query(DeceptionScenario).filter(DeceptionScenario.enabled == True).order_by(DeceptionScenario.priority.desc()).all()
        
        # We also want to support hardcoded fallbacks if DB is empty during testing
        hardcoded_scenarios = {
            "wp_admin": {
                "patterns": [r"wp-admin", r"wp-login", r"xmlrpc\.php"],
                "redirect_url": "/deception/wp-admin"
            },
            "database": {
                "patterns": [r"phpmyadmin", r"db_admin", r"\.sql", r"mysql"],
                "redirect_url": "/deception/phpmyadmin"
            },
            "leak": {
                "patterns": [r"\.env", r"config\.json", r"backup\.zip"],
                "redirect_url": "/deception/fake-leak"
            },
            "upload": {
                "patterns": [r"upload", r"\.php", r"\.jsp", r"\.asp"],
                "redirect_url": "/deception/fake-upload"
            },
            "login": {
                "patterns": [r"/login", r"auth", r"signin", r"credential"],
                "redirect_url": "/deception/fake-admin"
            }
        }
        
        # 1. Try DB Scenarios first
        for scenario in scenarios:
            for pattern in scenario.trigger_patterns:
                if re.search(pattern, endpoint, re.IGNORECASE) or re.search(pattern, payload, re.IGNORECASE):
                    # We assume the scenario_id maps to a route like /deception/{scenario_id}
                    return f"/deception/{scenario.scenario_id}"
                    
        # 2. Try Hardcoded
        for sc_id, sc_data in hardcoded_scenarios.items():
            for pattern in sc_data["patterns"]:
                if re.search(pattern, endpoint, re.IGNORECASE) or re.search(pattern, payload, re.IGNORECASE):
                    return sc_data["redirect_url"]
                    
        # 3. Fallback
        return "/deception/fake-admin"
        
    except Exception as e:
        logger.error(f"Error evaluating scenario: {e}")
        return "/deception/fake-admin"
    finally:
        db.close()
