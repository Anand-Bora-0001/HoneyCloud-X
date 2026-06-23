"""
Automated Integration & Unit Tests for HoneyCloud-X Email Alerts
"""
import sys
import os
import pytest
from unittest.mock import patch, MagicMock
import smtplib
from datetime import datetime
from fastapi.testclient import TestClient

# Add parent directory to path to import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
from app.services.email_service import email_service
from app.alert_system import handle_attack_event, send_telegram_alert, send_email_alert
from app.config import settings
from app.database import SessionLocal

client = TestClient(app)

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def auth_headers():
    login_response = client.post("/auth/login", data={
        "username": "admin",
        "password": "admin123"
    })
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@patch('smtplib.SMTP')
def test_smtp_sending(mock_smtp):
    """Test SMTP connection and successful delivery"""
    # Configure mock
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    # Enable email setting temporarily for unit test
    settings.email_enabled = True
    
    # Test sending email sync
    success = email_service.send_email_sync(
        to_emails=["anandbora241@gmail.com"],
        subject="Test Alert",
        html_body="<h1>Test html</h1>",
        text_body="Test fallback text"
    )
    
    assert success is True
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once()
    mock_server.send_message.assert_called_once()


def test_template_rendering():
    """Test HTML and plain-text templates render with SOC-style sections"""
    test_event = {
        'severity': 'CRITICAL',
        'source_ip': '101.100.180.2',
        'service': 'E-Commerce Frontend',
        'endpoint': '/admin/config',
        'method': 'POST',
        'timestamp': datetime.now().isoformat(),
        'threat_score': 0.92,
        'location': {
            'country': 'Germany',
            'city': 'Berlin',
            'flag': '🇩🇪',
            'isp': 'Leaseweb'
        },
        'command': 'cat /etc/shadow'
    }
    
    html = email_service._generate_alert_html("Critical Security Alert", test_event)
    text = email_service._generate_alert_text("Critical Security Alert", test_event)
    
    # Verify critical sections in HTML
    assert "CRITICAL Threat Level" in html
    assert "101.100.180.2" in html
    assert "E-Commerce Frontend" in html
    assert "cat /etc/shadow" in html
    assert "Germany" in html
    assert "Leaseweb" in html
    assert "T1552.001 - Credentials In Files" in html # MITRE mapping based on endpoint /admin/config
    assert "92/100" in html # Risk score
    assert "Recommended Incident Response" in html
    
    # Verify text fallback contains essentials
    assert "Severity: CRITICAL" in text
    assert "Source IP: 101.100.180.2" in text
    assert "Target Service: E-Commerce Frontend" in text


@patch('app.alert_system.send_telegram_alert')
@patch('app.alert_system.send_email_alert')
def test_pipeline_severity_routing(mock_send_email, mock_send_tg, db_session):
    """Test severity alert routing (Critical sends both, High sends email, Medium/Low skip)"""
    mock_send_email.return_value = True
    mock_send_tg.return_value = True
    
    # Enable channels in global settings
    settings.email_enabled = True
    settings.telegram_bot_token = "12345:dummy"
    settings.telegram_chat_id = "54321"
    
    critical_event = {
        'severity': 'CRITICAL',
        'source_ip': '1.2.3.4',
        'service': 'SSH',
        'organization_id': 1
    }
    
    high_event = {
        'severity': 'HIGH',
        'source_ip': '1.2.3.4',
        'service': 'SSH',
        'organization_id': 1
    }
    
    medium_event = {
        'severity': 'MEDIUM',
        'source_ip': '1.2.3.4',
        'service': 'SSH',
        'organization_id': 1
    }
    
    # Trigger CRITICAL alert -> expect both
    handle_attack_event(critical_event, db=db_session)
    assert mock_send_tg.called
    assert mock_send_email.called
    
    mock_send_tg.reset_mock()
    mock_send_email.reset_mock()
    
    # Trigger HIGH alert -> expect only Email
    handle_attack_event(high_event, db=db_session)
    assert not mock_send_tg.called
    assert mock_send_email.called
    
    mock_send_tg.reset_mock()
    mock_send_email.reset_mock()
    
    # Trigger MEDIUM alert -> expect neither
    handle_attack_event(medium_event, db=db_session)
    assert not mock_send_tg.called
    assert not mock_send_email.called


@patch('requests.post')
@patch('smtplib.SMTP')
def test_telegram_failure_does_not_block_email(mock_smtp, mock_post, db_session):
    """Test that Telegram delivery failure does not prevent Email alerts from executing"""
    # Telegram API fails
    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_post.return_value = mock_response
    
    # SMTP succeeds
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    settings.email_enabled = True
    settings.telegram_bot_token = "12345:dummy"
    settings.telegram_chat_id = "54321"
    
    critical_event = {
        'severity': 'CRITICAL',
        'source_ip': '1.2.3.4',
        'service': 'SSH',
        'organization_id': 1
    }
    
    # Execute routing
    handle_attack_event(critical_event, db=db_session)
    
    # SMTP should still be called
    mock_server.send_message.assert_called_once()


@patch('requests.post')
@patch('smtplib.SMTP')
def test_email_failure_does_not_block_telegram(mock_smtp, mock_post, db_session):
    """Test that Email delivery failure does not prevent Telegram alerts from executing"""
    # Telegram API succeeds
    mock_response = MagicMock()
    mock_response.ok = True
    mock_post.return_value = mock_response
    
    # SMTP fails
    mock_smtp.side_effect = smtplib.SMTPConnectError(550, "Failed connection")
    
    settings.email_enabled = True
    settings.telegram_bot_token = "12345:dummy"
    settings.telegram_chat_id = "54321"
    
    critical_event = {
        'severity': 'CRITICAL',
        'source_ip': '1.2.3.4',
        'service': 'SSH',
        'organization_id': 1
    }
    
    # Execute routing
    handle_attack_event(critical_event, db=db_session)
    
    # Telegram should still be called
    assert mock_post.called


@patch('smtplib.SMTP')
def test_smtp_credentials_error_handling(mock_smtp):
    """Test that invalid SMTP credentials are caught and logged without exposure"""
    mock_server = MagicMock()
    # Mock SMTP authentication failure
    mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    settings.email_enabled = True
    
    success = email_service.send_email_sync(
        to_emails=["anandbora241@gmail.com"],
        subject="Credential Fail Test",
        html_body="<p>Test</p>"
    )
    
    assert success is False
    # Ensure it didn't raise exception upward, handled internally


@patch('smtplib.SMTP')
def test_smtp_timeout_and_retries(mock_smtp):
    """Test that SMTP timeout triggers the configured retries before failing"""
    # Mock connection timeout on socket
    mock_smtp.side_effect = TimeoutError("SMTP connection timed out")
    
    settings.email_enabled = True
    # Temporarily speed up retry delay for fast test execution
    email_service.retry_delay = 0.01
    
    success = email_service.send_email_sync(
        to_emails=["anandbora241@gmail.com"],
        subject="Timeout Test",
        html_body="<p>Test</p>"
    )
    
    assert success is False
    # Verifies it retried 3 times (the initial attempt + 2 retries)
    assert mock_smtp.call_count == 3


def test_api_config_routes(auth_headers):
    """Test fetching and saving notification settings via API endpoints"""
    # 1. Fetch current config
    response = client.get("/api/alerts/config", headers=auth_headers)
    assert response.status_code == 200
    config_data = response.json()
    assert "email_enabled" in config_data
    assert "daily_summary_enabled" in config_data
    assert "weekly_report_enabled" in config_data
    
    # 2. Update config preferences
    new_pref = {
        "telegram_enabled": True,
        "email_enabled": True,
        "alert_on_critical": True,
        "alert_on_high": True,
        "alert_on_medium": False,
        "alert_on_low": False,
        "daily_summary_enabled": True,
        "weekly_report_enabled": False,
        "saved_emails": ["test_admin@honeycloud.local"]
    }
    
    post_response = client.post("/api/alerts/config", json=new_pref, headers=auth_headers)
    assert post_response.status_code == 200
    assert post_response.json()["status"] == "success"
    
    # 3. Verify it saved correctly
    get_response = client.get("/api/alerts/config", headers=auth_headers)
    assert get_response.status_code == 200
    saved_data = get_response.json()
    assert saved_data["telegram_enabled"] is True
    assert saved_data["email_enabled"] is True
    assert saved_data["daily_summary_enabled"] is True
    assert saved_data["weekly_report_enabled"] is False
    assert "test_admin@honeycloud.local" in saved_data["saved_emails"]
