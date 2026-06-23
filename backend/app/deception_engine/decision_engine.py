# backend/app/deception_engine/decision_engine.py
from .threat_context import ThreatContext
from .risk_profiles import RiskProfileManager

class DecisionEngine:
    """
    Evaluates the threat context to make a routing decision.
    """
    
    @classmethod
    def evaluate(cls, context: ThreatContext) -> dict:
        """
        Returns a decision dictionary:
        {
            "recommended_route": "CONTINUE" | "DECEPTION" | "BLOCK",
            "confidence": float,
            "reasoning": str
        }
        """
        
        # Base routing defaults
        route = "CONTINUE"
        confidence = 0.5
        reasoning = "Normal traffic pattern."
        
        # Update risk level based on latest score
        context.risk_level = RiskProfileManager.calculate_risk_level(context.threat_score)
        
        # Behavioral analysis
        if context.risk_level == "CRITICAL":
            route = "DECEPTION"
            confidence = 0.95
            reasoning = "Critical threat score exceeded threshold."
            
        elif context.risk_level == "HIGH":
            # Check for fast-paced scanning
            if context.metrics["total_requests"] > 20 and len(context.metrics["unique_endpoints"]) > 10:
                route = "DECEPTION"
                confidence = 0.85
                reasoning = "High threat score combined with aggressive endpoint enumeration."
            else:
                # Still HIGH risk, but maybe targeted. Deception is recommended.
                route = "DECEPTION"
                confidence = 0.75
                reasoning = "High threat score detected."
                
        elif context.metrics["failed_auths"] > 5:
            route = "DECEPTION"
            confidence = 0.80
            reasoning = "Brute force pattern detected."
            
        # Exception: if it's already blocked by WAF/other means, we might route to BLOCK, 
        # but for Phase 1 Deception, we either CONTINUE or DECEPTION.
        
        return {
            "recommended_route": route,
            "confidence": confidence,
            "reasoning": reasoning
        }
