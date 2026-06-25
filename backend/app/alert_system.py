"""
HoneyCloud Alert System with Real Email Integration
Handles Telegram and Email notifications with PDF reports
"""
import logging
import requests
import os
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from .config import settings
from .services.email_service import email_service

logger = logging.getLogger(__name__)

def _update_notification_stats(db: Session, organization_id: int, channel: str, success: bool):
    if not db or not organization_id:
        return
    try:
        from .models import NotificationConfig
        config = db.query(NotificationConfig).filter(
            NotificationConfig.organization_id == organization_id
        ).first()
        if config:
            if success:
                if channel == "telegram":
                    config.telegram_alerts_sent += 1
                    config.last_telegram_sent_at = datetime.now()
                elif channel == "email":
                    config.email_alerts_sent += 1
                    config.last_email_sent_at = datetime.now()
            else:
                config.failed_deliveries += 1
            db.commit()
    except Exception as e:
        logger.warning(f"Failed to update notification stats in DB: {e}")

def send_telegram_alert(message: str, db: Session = None, organization_id: int = None) -> bool:
    """Send alert message to Telegram using organization's configuration"""
    success = False
    try:
        # Try to get configuration from database first
        if db and organization_id:
            from .models import NotificationConfig
            config = db.query(NotificationConfig).filter(
                NotificationConfig.organization_id == organization_id,
                NotificationConfig.telegram_enabled == True
            ).first()
            
            if config and config.telegram_bot_token and config.telegram_chat_id:
                url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
                payload = {
                    'chat_id': config.telegram_chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }
                
                response = requests.post(url, json=payload, timeout=10)
                
                if response.ok:
                    logger.info("✅ Telegram alert sent successfully (database config)")
                    success = True
                else:
                    logger.error(f"❌ Telegram alert failed: {response.status_code} - {response.text}")
    except Exception as e:
        logger.warning(f"Database Telegram config failed: {e}")
    
    if not success:
        # Fallback to global settings
        if not settings.is_telegram_configured:
            logger.warning("Telegram not configured - skipping alert")
            if db and organization_id:
                _update_notification_stats(db, organization_id, "telegram", False)
            return False
        
        try:
            url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
            payload = {
                'chat_id': settings.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.ok:
                logger.info("✅ Telegram alert sent successfully (global config)")
                success = True
            else:
                logger.error(f"❌ Telegram alert failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Telegram alert error: {e}")
            
    if db and organization_id:
        _update_notification_stats(db, organization_id, "telegram", success)
    return success

def send_telegram_document(file_path: str, caption: str = "", db: Session = None, organization_id: int = None) -> bool:
    """Send document to Telegram using organization's configuration"""
    try:
        # Try to get configuration from database first
        if db and organization_id:
            from .models import NotificationConfig
            config = db.query(NotificationConfig).filter(
                NotificationConfig.organization_id == organization_id,
                NotificationConfig.telegram_enabled == True
            ).first()
            
            if config and config.telegram_bot_token and config.telegram_chat_id:
                if not os.path.exists(file_path):
                    logger.error(f"❌ File not found: {file_path}")
                    return False
                
                url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendDocument"
                
                with open(file_path, 'rb') as file:
                    files = {'document': file}
                    data = {
                        'chat_id': config.telegram_chat_id,
                        'caption': caption
                    }
                    
                    response = requests.post(url, files=files, data=data, timeout=30)
                
                if response.ok:
                    logger.info(f"✅ Telegram document sent: {os.path.basename(file_path)} (database config)")
                    return True
                else:
                    logger.error(f"❌ Telegram document failed: {response.status_code} - {response.text}")
                    return False
    except Exception as e:
        logger.warning(f"Database Telegram document failed: {e}")
    
    # Fallback to global settings
    if not settings.is_telegram_configured:
        logger.warning("Telegram not configured - skipping document")
        return False
    
    if not os.path.exists(file_path):
        logger.error(f"❌ File not found: {file_path}")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendDocument"
        
        with open(file_path, 'rb') as file:
            files = {'document': file}
            data = {
                'chat_id': settings.telegram_chat_id,
                'caption': caption
            }
            
            response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.ok:
            logger.info(f"✅ Telegram document sent: {os.path.basename(file_path)} (global config)")
            return True
        else:
            logger.error(f"❌ Telegram document failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Telegram document error: {e}")
        return False

def send_email_alert(
    to_emails: List[str],
    alert_type: str,
    event_data: dict,
    pdf_report_path: Optional[str] = None,
    db: Session = None,
    organization_id: int = None
) -> bool:
    """
    Send professional email alert with PDF report
    """
    if not email_service.is_configured():
        logger.warning("Email service not configured - skipping alert")
        if db and organization_id:
            _update_notification_stats(db, organization_id, "email", False)
        return False
    
    try:
        success = email_service.send_alert_email(
            to_emails=to_emails,
            alert_type=alert_type,
            event_data=event_data,
            pdf_report_path=pdf_report_path
        )
        
        if success:
            logger.info(f"✅ Email alert sent to {', '.join(to_emails)}")
        else:
            logger.error("❌ Failed to send email alert")
        
        if db and organization_id:
            _update_notification_stats(db, organization_id, "email", success)
        return success
        
    except Exception as e:
        logger.error(f"❌ Email alert error: {e}")
        if db and organization_id:
            _update_notification_stats(db, organization_id, "email", False)
        return False

def handle_attack_event(event: dict, db: Session = None) -> None:
    """
    Handle incoming attack event and trigger appropriate alerts
    """
    try:
        severity = event.get('severity', 'UNKNOWN')
        source_ip = event.get('source_ip', 'Unknown')
        service = event.get('service', 'Unknown')
        organization_id = event.get('organization_id')
        
        logger.info(f"🚨 Processing {severity} alert from {source_ip} on {service} (Org: {organization_id})")
        
        # Load default settings
        email_enabled = settings.email_enabled
        telegram_enabled = settings.is_telegram_configured
        
        alert_on_critical = True
        alert_on_high = True
        alert_on_medium = False
        alert_on_low = False
        
        recipients = [settings.alert_email_to] if settings.alert_email_to else []
        
        if db and organization_id:
            try:
                from .models import NotificationConfig
                config = db.query(NotificationConfig).filter(
                    NotificationConfig.organization_id == organization_id
                ).first()
                if config:
                    telegram_enabled = config.telegram_enabled
                    email_enabled = config.email_enabled
                    recipients = config.email_addresses or []
                    alert_on_critical = config.alert_on_critical
                    alert_on_high = config.alert_on_high
                    alert_on_medium = config.alert_on_medium
                    alert_on_low = config.alert_on_low
            except Exception as e:
                logger.warning(f"Failed to fetch NotificationConfig from DB: {e}")

        # Check severity threshold filters
        severity_match = False
        if severity == 'CRITICAL' and alert_on_critical:
            severity_match = True
        elif severity == 'HIGH' and alert_on_high:
            severity_match = True
        elif severity == 'MEDIUM' and alert_on_medium:
            severity_match = True
        elif severity == 'LOW' and alert_on_low:
            severity_match = True
            
        if not severity_match:
            logger.info(f"Skipping alert: severity {severity} does not match configured thresholds")
            return
            
        # Parallel Routing Rules:
        # Telegram: On CRITICAL severity OR when deception is recommended (i.e. trapped an attacker)
        send_tg = telegram_enabled and (severity == 'CRITICAL' or event.get('recommended_route') == 'DECEPTION')
        
        # Email: On CRITICAL and HIGH severity
        send_mail = email_enabled and (severity in ['CRITICAL', 'HIGH'])
        
        # Async vs Sync Celery handling
        from .worker import CELERY_AVAILABLE
        from .tasks.alert_tasks import send_telegram_alert_async, send_email_alert_async
        
        if send_tg:
            alert_message = generate_alert_message(event)
            if CELERY_AVAILABLE:
                send_telegram_alert_async.delay(alert_message, organization_id=organization_id)
            else:
                send_telegram_alert(alert_message, db=db, organization_id=organization_id)
                
        if send_mail and recipients:
            pdf_path = None
            try:
                from .report_generator import generate_pdf_report
                pdf_path = generate_pdf_report([event], {'total_events': 1, 'events_by_severity': {severity: 1}})
            except Exception as e:
                logger.error(f"Failed to generate PDF report: {e}")
                
            if CELERY_AVAILABLE:
                send_email_alert_async.delay(
                    to_emails=recipients,
                    alert_type=f"{severity} Incident Report",
                    event_data=event,
                    pdf_path=pdf_path
                )
            else:
                send_email_alert(
                    to_emails=recipients,
                    alert_type=f"{severity} Incident Report",
                    event_data=event,
                    pdf_report_path=pdf_path,
                    db=db,
                    organization_id=organization_id
                )
        
        logger.info(f"✅ Alert processing delegated (Async: {CELERY_AVAILABLE})")
        
    except Exception as e:
        logger.error(f"❌ Error handling attack event: {e}")

def generate_alert_message(event: dict) -> str:
    """Generate formatted alert message for Telegram"""
    severity = event.get('severity', 'UNKNOWN')
    source_ip = event.get('source_ip', 'Unknown')
    service = event.get('service', 'Unknown')
    endpoint = event.get('endpoint', 'N/A')
    timestamp = event.get('timestamp', datetime.now().isoformat())
    location = event.get('location', {})
    
    # Severity emoji mapping
    severity_emojis = {
        'CRITICAL': '🔴',
        'HIGH': '🟠',
        'MEDIUM': '🟡',
        'LOW': '🟢'
    }
    
    emoji = severity_emojis.get(severity, '⚪')
    flag = location.get('flag', '🌍')
    country = location.get('country', 'Unknown')
    city = location.get('city', 'Unknown')
    
    message = f"""
🚨 <b>HoneyCloud Security Alert</b>

{emoji} <b>Severity:</b> {severity}
🎯 <b>Service:</b> {service}
🌐 <b>Source IP:</b> <code>{source_ip}</code>
📍 <b>Location:</b> {flag} {city}, {country}
🔗 <b>Endpoint:</b> {endpoint}
⏰ <b>Time:</b> {timestamp}

🛡️ <b>Threat detected and logged</b>
📊 Check dashboard for details
    """
    
    return message.strip()

# Backward compatibility functions
def format_alert_message(event: dict) -> str:
    """Legacy function - use generate_alert_message instead"""
    return generate_alert_message(event)

def send_comprehensive_alert(event: dict, alert_type: str = "telegram"):
    """Send comprehensive alert with PDF report"""
    try:
        # Generate mini report for this specific event
        mini_report_data = {
            "total_events": 1,
            "events_by_service": {event.get("service", "Unknown"): 1},
            "events_by_severity": {event.get("severity", "Unknown"): 1},
            "ai_labels": {event.get("ai_label", "unknown"): 1}
        }
        
        # Generate PDF report
        from .report_generator import generate_pdf_report
        pdf_path = generate_pdf_report([event], mini_report_data)
        
        if alert_type == "telegram":
            # Send detailed message with PDF
            message = generate_alert_message(event)
            send_telegram_alert(message)
            send_telegram_document(pdf_path, f"Security Alert Report - Event #{event.get('id')}")
        elif alert_type == "email":
            # Send email alert (would need recipient list)
            logger.info("Email alert requested but no recipients specified")
        
        logger.info(f"📄 Comprehensive {alert_type} alert sent with PDF report")
        
    except Exception as e:
        logger.error(f"❌ Failed to send comprehensive alert: {e}")

def send_test_telegram_alert() -> bool:
    """Send test Telegram alert"""
    test_message = f"""
🧪 <b>HoneyCloud Test Alert</b>

✅ <b>System Status:</b> All systems operational
📊 <b>Monitoring:</b> Active
🔔 <b>Alerts:</b> Configured and working
⏰ <b>Test Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is a test message from HoneyCloud Security Monitoring.
    """
    
    return send_telegram_alert(test_message)

def send_test_email_alert(to_emails: List[str]) -> bool:
    """Send test email alert"""
    test_event = {
        'severity': 'HIGH',
        'source_ip': '192.168.1.100',
        'service': 'TEST',
        'endpoint': '/test-alert',
        'method': 'GET',
        'timestamp': datetime.now().isoformat(),
        'location': {
            'country': 'Test Country',
            'city': 'Test City',
            'flag': '🧪',
            'isp': 'Test ISP'
        }
    }
    
    return send_email_alert(
        to_emails=to_emails,
        alert_type="Test Security Alert",
        event_data=test_event
    )
