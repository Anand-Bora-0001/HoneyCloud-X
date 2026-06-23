import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, engine, Base
from app.models import DeceptionSession, AttackerProfile, Service, Organization

client = TestClient(app)

@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    
def test_missing_api_key():
    response = client.post("/api/ingest", json={"source_ip": "1.2.3.4", "severity": "LOW"})
    assert response.status_code == 401
    assert "API Key required" in response.json()["detail"]

def test_invalid_api_key():
    response = client.post("/api/ingest", json={"source_ip": "1.2.3.4"}, headers={"X-API-Key": "invalid_key"})
    assert response.status_code == 401
    assert "Invalid API Key" in response.json()["detail"]

def test_valid_demo_api_key(test_db):
    event_data = {
        "service": "HTTP",
        "source_ip": "8.8.8.8",
        "severity": "LOW",
        "endpoint": "/",
        "method": "GET"
    }
    response = client.post(
        "/api/ingest", 
        json=event_data, 
        headers={"X-API-Key": "hc_live_fsj-onia9stXSc2HgIuUDqfwR_f5Oe0Q4sTZTMhBku0"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "received"
    
    # Wait briefly for background task
    import time
    time.sleep(1)
    
    # Check session was created
    session = test_db.query(DeceptionSession).filter_by(source_ip="8.8.8.8").first()
    assert session is not None
    assert session.recommended_route in ["CONTINUE", "DECEPTION"]
    
    # Check profile was created
    profile = test_db.query(AttackerProfile).filter_by(source_ip="8.8.8.8").first()
    assert profile is not None
    assert profile.total_attacks > 0

def test_deception_routing(test_db):
    # Simulate aggressive attack to trigger DECEPTION route
    for i in range(25):
        event_data = {
            "service": "HTTP",
            "source_ip": "9.9.9.9",
            "severity": "HIGH",
            "endpoint": f"/admin/config_{i}.php",
            "method": "GET"
        }
        client.post(
            "/api/ingest", 
            json=event_data, 
            headers={"X-API-Key": "hc_live_fsj-onia9stXSc2HgIuUDqfwR_f5Oe0Q4sTZTMhBku0"}
        )
    
    import time
    time.sleep(2)
    
    session = test_db.query(DeceptionSession).filter_by(source_ip="9.9.9.9").order_by(DeceptionSession.id.desc()).first()
    assert session is not None
    assert session.risk_level in ["HIGH", "CRITICAL"]
    assert session.recommended_route == "DECEPTION"
