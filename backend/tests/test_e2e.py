import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import AttackerProfile, DeceptionSession, DeceptionAction, InvestigationReport
import time

client = TestClient(app)

def test_full_attack_lifecycle():
    # 1. Simulate an attack on /api/ingest
    payload = {
        "endpoint": "/wp-login.php",
        "method": "POST",
        "severity": "HIGH",
        "source_ip": "192.168.100.100",
        "timestamp": "2026-06-22T10:00:00Z"
    }
    headers = {"X-API-Key": "hc_live_fsj-onia9stXSc2HgIuUDqfwR_f5Oe0Q4sTZTMhBku0"}
    response = client.post("/api/ingest", json=payload, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "redirect_url" in data
    assert "wp-admin" in data["redirect_url"]
    
    # Extract session ID from the redirect url if possible, but actually the session is created asynchronously.
    # Let's wait a moment for the async task to create the session and profile.
    time.sleep(1.0)
    
    db = SessionLocal()
    profile = db.query(AttackerProfile).filter_by(source_ip="192.168.100.100").first()
    assert profile is not None
    
    session = db.query(DeceptionSession).filter_by(source_ip="192.168.100.100").first()
    assert session is not None
    
    # 2. Simulate hitting the fake WP Admin trap
    wp_response = client.get(f"/deception/wp-admin?sid={session.session_id}")
    assert wp_response.status_code == 200
    
    # Wait for the background tracking task
    time.sleep(1.0)
    
    action = db.query(DeceptionAction).filter_by(session_id=session.session_id, action_type="VIEW_WP_ADMIN").first()
    assert action is not None
    
    # 3. Simulate an upload trap
    file_content = b"fake payload"
    files = {"file": ("malware.php", file_content, "application/x-httpd-php")}
    upload_resp = client.post(f"/deception/fake-upload?sid={session.session_id}", files=files)
    assert upload_resp.status_code == 200
    
    # 4. Trigger an investigation (usually happens via async on persona update)
    from backend.app.investigation_engine.investigation_service import InvestigationService
    report = InvestigationService.run_investigation(db, profile.id)
    assert report is not None
    assert "malware.php" in str(report.evidence_summary)
    
    db.close()
