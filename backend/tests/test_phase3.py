import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import DeceptionScenario, FakeAsset, FileUploadAttempt, AttackerProfile, DeceptionAction
import uuid

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    db = SessionLocal()
    # Ensure test org and service exist if needed, otherwise rely on demo fallback
    yield
    db.close()

def test_scenario_routing_wp():
    """Test that a request to /wp-admin returns a redirect URL to /deception/wp-admin"""
    payload = {
        "endpoint": "/wp-login.php",
        "method": "POST",
        "severity": "HIGH",
        "timestamp": "2026-01-01T12:00:00Z"
    }
    # Using the demo api key for simplicity
    headers = {"X-API-Key": "hc_live_fsj-onia9stXSc2HgIuUDqfwR_f5Oe0Q4sTZTMhBku0"}
    response = client.post("/api/ingest", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "redirect_url" in data
    assert "wp-admin" in data["redirect_url"]

def test_scenario_routing_db():
    """Test that a request to /phpmyadmin returns a redirect URL to /deception/phpmyadmin"""
    payload = {
        "endpoint": "/phpmyadmin/index.php",
        "method": "GET",
        "severity": "HIGH",
        "timestamp": "2026-01-01T12:00:00Z"
    }
    headers = {"X-API-Key": "hc_live_fsj-onia9stXSc2HgIuUDqfwR_f5Oe0Q4sTZTMhBku0"}
    response = client.post("/api/ingest", json=payload, headers=headers)
    assert response.status_code == 200
    assert "phpmyadmin" in response.json()["redirect_url"]

def test_fake_upload_trap():
    """Test that file uploads are tracked but not stored"""
    db = SessionLocal()
    from backend.app.models import DeceptionSession
    # Ensure session exists
    session = DeceptionSession(
        session_id="test_session_123",
        organization_id=1,
        source_ip="10.0.0.1",
        risk_level="HIGH"
    )
    db.merge(session)
    db.commit()
    db.close()
    
    file_content = b"malicious shell payload"
    files = {"file": ("shell.php", file_content, "application/x-httpd-php")}
    
    response = client.post("/deception/fake-upload?sid=test_session_123", files=files)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify DB insertion
    db = SessionLocal()
    upload = db.query(FileUploadAttempt).filter_by(filename="shell.php").first()
    assert upload is not None
    assert upload.size == len(file_content)
    assert upload.file_hash is not None
    
    # Cleanup
    db.delete(upload)
    db.commit()
    db.close()

def test_persona_engine():
    """Test Persona calculation logic"""
    from backend.app.deception_engine.persona_engine import PersonaEngine
    
    db = SessionLocal()
    
    # Create fake actions
    actions = [
        DeceptionAction(action_type="VIEW_WP_ADMIN"),
        DeceptionAction(action_type="WP_AUTH_ATTEMPT"),
        DeceptionAction(action_type="WP_AUTH_ATTEMPT")
    ]
    
    profile = AttackerProfile(
        organization_id=1,
        source_ip="10.0.0.1",
        persona="Scanner",
        confidence_score=0.5
    )
    
    PersonaEngine.update_profile_persona(profile, actions)
    assert profile.persona == "Credential Hunter"
    assert profile.confidence_score > 0.6
    
    # Add Data Thief behavior
    actions.append(DeceptionAction(action_type="FILE_UPLOAD_ATTEMPT"))
    PersonaEngine.update_profile_persona(profile, actions)
    assert profile.persona == "Persistence Seeker"
    
    db.close()
