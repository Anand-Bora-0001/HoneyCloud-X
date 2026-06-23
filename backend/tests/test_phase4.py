import pytest
from backend.app.investigation_engine.mitre_mapper import MitreMapper
from backend.app.investigation_engine.profile_builder import ProfileBuilder
from backend.app.investigation_engine.timeline_analyzer import TimelineAnalyzer
from backend.app.investigation_engine.evidence_collector import EvidenceCollector
from backend.app.models import AttackerProfile, DeceptionAction, FileUploadAttempt, DeceptionSession
from datetime import datetime, timedelta

def test_mitre_mapper():
    actions = ["WP_AUTH_ATTEMPT", "DIRECTORY_SCAN", "FILE_UPLOAD_ATTEMPT", "UNKNOWN_ACTION"]
    mapping = MitreMapper.map_actions(actions)
    
    assert "T1110.001" in mapping
    assert "T1083" in mapping
    assert "T1505.003" in mapping
    assert len(mapping) == 3

def test_profile_builder_narrative():
    evidence = {
        "total_sessions": 3,
        "persona": "Data Thief",
        "login_attempts": 0,
        "upload_attempts": 0,
        "exports_attempted": 5,
        "honey_tokens_triggered": 2,
        "most_targeted_endpoint": "/api/v1/customers",
        "confidence": 0.95
    }
    
    narrative = ProfileBuilder.generate_narrative(evidence)
    
    assert "returned 3 times" in narrative
    assert "data exfiltration intent" in narrative
    assert "triggering 2 honey tokens" in narrative
    assert "/api/v1/customers" in narrative
    assert "Confidence: 95%" in narrative

def test_timeline_analyzer():
    now = datetime.utcnow()
    actions = [
        DeceptionAction(timestamp=now, action_type="SCAN", endpoint="/"),
        DeceptionAction(timestamp=now + timedelta(seconds=10), action_type="WP_AUTH_ATTEMPT", endpoint="/wp-admin"),
        DeceptionAction(timestamp=now + timedelta(seconds=40), action_type="FILE_UPLOAD_ATTEMPT", endpoint="/fake-upload")
    ]
    
    timeline = TimelineAnalyzer.analyze_actions(actions)
    
    assert timeline["dwell_time_seconds"] == 40
    assert timeline["total_nodes"] == 3
    assert timeline["attack_paths"][0]["from"] == "External"
    assert timeline["attack_paths"][0]["to"] == "/"
    assert timeline["attack_paths"][1]["from"] == "/"
    assert timeline["attack_paths"][1]["to"] == "/wp-admin"

def test_risk_trend():
    now = datetime.utcnow()
    sessions = [
        DeceptionSession(started_at=now, threat_score=30.0),
        DeceptionSession(started_at=now + timedelta(hours=1), threat_score=50.0),
        DeceptionSession(started_at=now + timedelta(hours=2), threat_score=85.0)
    ]
    
    trend = ProfileBuilder.calculate_risk_trend(sessions)
    assert trend["trend"] == "Escalating"
    assert trend["last_score"] == 85.0
