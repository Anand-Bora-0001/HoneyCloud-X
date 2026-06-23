import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal, Base, engine
from backend.app.models import DeceptionSession, DeceptionAction, Organization, Service

client = TestClient(app)

@pytest.fixture(autouse=True)
def db_setup():
    # Setup test DB
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Create demo org and service if not exists
    org = db.query(Organization).first()
    if not org:
        org = Organization(name="Test Org", slug="test-org", email="test@test.com")
        db.add(org)
        db.commit()
        db.refresh(org)
        
    service = db.query(Service).first()
    if not service:
        service = Service(name="Test Service", slug="test-svc", api_key="test-api-key", organization_id=org.id)
        db.add(service)
        db.commit()
        db.refresh(service)
        
    session = db.query(DeceptionSession).filter(DeceptionSession.session_id == "test_sess_123").first()
    if not session:
        session = DeceptionSession(
            session_id="test_sess_123",
            source_ip="127.0.0.1",
            organization_id=org.id,
            service_id=service.id,
            status="ACTIVE",
            recommended_route="DECEPTION"
        )
        db.add(session)
        db.commit()
    
    yield db
    
    # Cleanup
    db.query(DeceptionAction).filter(DeceptionAction.session_id == "test_sess_123").delete()
    db.query(DeceptionSession).filter(DeceptionSession.session_id == "test_sess_123").delete()
    db.commit()
    db.close()

def test_deception_admin_view():
    response = client.get("/deception/fake-admin?sid=test_sess_123")
    assert response.status_code == 200
    assert "Corporate Administration Panel" in response.text
    assert "Monthly Revenue" in response.text
    
    # Verify tracking action
    db = SessionLocal()
    action = db.query(DeceptionAction).filter(DeceptionAction.session_id == "test_sess_123").first()
    assert action is not None
    assert action.action_type == "VIEW_ADMIN_DASHBOARD"
    assert action.endpoint == "/deception/fake-admin"
    db.close()

def test_deception_products_view():
    response = client.get("/deception/fake-products")
    assert response.status_code == 200
    assert "Enterprise Firewall Appliance" in response.text

def test_deception_customers_view():
    response = client.get("/deception/fake-customers")
    assert response.status_code == 200
    assert "Global Tech" in response.text

def test_deception_export_csv():
    response = client.get("/deception/export/customers")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment; filename=customers_backup.csv" in response.headers["content-disposition"]
    assert "id,name,email,spend" in response.text
    assert "CUST-001" in response.text
