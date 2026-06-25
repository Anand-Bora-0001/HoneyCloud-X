"""
Alert testing routes (Telegram + Email).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import re
import logging

from ..deps import get_current_user, get_db
from ...config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

# Simple global storage for saved emails
saved_emails = []


@router.post("/test-telegram")
async def test_telegram_alert(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send test alert to Telegram with PDF report"""
    try:
        from .events import get_events, get_statistics
        from ...report_generator import generate_pdf_report
        from ...alert_system import send_telegram_alert, send_telegram_document

        events_response = get_events(limit=10, current_user=current_user, db=db)
        stats_response = get_statistics(current_user, db)
        pdf_path = generate_pdf_report(events_response, stats_response)

        alert_message = f"""
🚨 *HoneyCloud Test Alert*

📊 *System Status:*
• Total Events: {stats_response.get('total_events', 0)}
• Critical Alerts: {stats_response.get('events_by_severity', {}).get('CRITICAL', 0)}

⏰ *Test Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        org_id = current_user.get("organization_id")
        message_sent = send_telegram_alert(alert_message, db=db, organization_id=org_id)
        pdf_sent = False
        if message_sent and pdf_path:
            pdf_sent = send_telegram_document(pdf_path, "🍯 HoneyCloud Security Report", db=db, organization_id=org_id)

        if message_sent:
            return {"status": "success", "message": "Test alert sent!", "pdf_sent": pdf_sent}
        return {"status": "error", "message": "Failed to send Telegram alert."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Telegram alert failed: {str(e)}")


@router.post("/test-email")
async def test_email_alert(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send test email alert with PDF report"""
    try:
        global saved_emails

        email_address = request.get("email_address")
        save_email = request.get("save_email", False)

        if not email_address:
            raise HTTPException(status_code=400, detail="Email address is required")

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email_address):
            raise HTTPException(status_code=400, detail="Invalid email format")

        if save_email and email_address not in saved_emails:
            saved_emails.append(email_address)

        from .events import get_events, get_statistics
        from ...report_generator import generate_pdf_report

        events_response = get_events(limit=20, current_user=current_user, db=db)
        stats_response = get_statistics(current_user, db)
        pdf_path = None
        try:
            pdf_path = generate_pdf_report(events_response, stats_response)
        except Exception as e:
            logger.warning(f"Test email PDF generation failed: {e}")

        try:
            from ...services.email_service import email_service
            if not email_service.is_configured():
                raise Exception("SMTP is not configured in .env. Please configure SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD.")

            test_event = {
                'severity': 'HIGH', 'source_ip': '192.168.1.100',
                'service': 'TEST-NODE', 'endpoint': '/test-alert',
                'method': 'GET', 'timestamp': datetime.now().isoformat(),
                'location': {'country': 'Test Country', 'city': 'Test City', 'flag': '🧪', 'isp': 'Test ISP'}
            }
            
            # Send synchronously to catch exact exception for detailed error logs
            success = email_service.send_email_sync(
                to_emails=[email_address],
                subject="🚨 HoneyCloud Test Threat Alert",
                html_body=email_service._generate_alert_html("Test Security Alert", test_event),
                text_body=email_service._generate_alert_text("Test Security Alert", test_event),
                attachments=[pdf_path] if pdf_path else None
            )
            
            if success:
                if save_email and db:
                    from ...models import User, NotificationConfig
                    user = db.query(User).filter(User.username == current_user["username"]).first()
                    if user:
                        config = db.query(NotificationConfig).filter(
                            NotificationConfig.organization_id == user.organization_id
                        ).first()
                        if config:
                            current_emails = config.email_addresses or []
                            if email_address not in current_emails:
                                current_emails.append(email_address)
                                config.email_addresses = current_emails
                                db.commit()
                return {"status": "success", "message": "Email Sent Successfully", "pdf_attached": bool(pdf_path)}
            else:
                return {"status": "error", "message": "Email Delivery Failed", "details": "SMTP login succeeded but send failed. Check server logs."}
                
        except Exception as smtp_err:
            logger.error(f"SMTP error: {smtp_err}")
            return {"status": "error", "message": "Email Delivery Failed", "details": str(smtp_err)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email alert failed: {str(e)}")


@router.get("/config")
async def get_alert_config(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current alert configuration"""
    try:
        from ...models import User, NotificationConfig
        if db:
            user = db.query(User).filter(User.username == current_user["username"]).first()
            if user and hasattr(user, 'organization') and user.organization:
                config = db.query(NotificationConfig).filter(
                    NotificationConfig.organization_id == user.organization_id
                ).first()
                if config:
                    return {
                        "telegram_enabled": config.telegram_enabled,
                        "email_enabled": config.email_enabled,
                        "saved_emails": config.email_addresses or [],
                        "alert_on_critical": config.alert_on_critical,
                        "alert_on_high": config.alert_on_high,
                        "alert_on_medium": config.alert_on_medium,
                        "alert_on_low": config.alert_on_low,
                        "daily_summary_enabled": config.daily_summary_enabled,
                        "weekly_report_enabled": config.weekly_report_enabled
                    }
    except Exception as e:
        logger.warning(f"DB alert config failed: {e}")

    return {
        "telegram_enabled": False,
        "email_enabled": len(saved_emails) > 0,
        "saved_emails": saved_emails,
        "alert_on_critical": True,
        "alert_on_high": True,
        "alert_on_medium": False,
        "alert_on_low": False,
        "daily_summary_enabled": False,
        "weekly_report_enabled": False
    }


@router.post("/config")
async def save_alert_config(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save alert configuration"""
    try:
        from ...models import User, NotificationConfig
        user = db.query(User).filter(User.username == current_user["username"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        config = db.query(NotificationConfig).filter(
            NotificationConfig.organization_id == user.organization_id
        ).first()
        
        if not config:
            config = NotificationConfig(
                organization_id=user.organization_id,
                email_enabled=request.get("email_enabled", True),
                email_addresses=request.get("saved_emails", []),
                telegram_enabled=request.get("telegram_enabled", False),
                alert_on_critical=request.get("alert_on_critical", True),
                alert_on_high=request.get("alert_on_high", True),
                alert_on_medium=request.get("alert_on_medium", False),
                alert_on_low=request.get("alert_on_low", False),
                daily_summary_enabled=request.get("daily_summary_enabled", False),
                weekly_report_enabled=request.get("weekly_report_enabled", False)
            )
            db.add(config)
        else:
            if "email_enabled" in request:
                config.email_enabled = request["email_enabled"]
            if "saved_emails" in request:
                config.email_addresses = request["saved_emails"]
            if "telegram_enabled" in request:
                config.telegram_enabled = request["telegram_enabled"]
            if "alert_on_critical" in request:
                config.alert_on_critical = request["alert_on_critical"]
            if "alert_on_high" in request:
                config.alert_on_high = request["alert_on_high"]
            if "alert_on_medium" in request:
                config.alert_on_medium = request["alert_on_medium"]
            if "alert_on_low" in request:
                config.alert_on_low = request["alert_on_low"]
            if "daily_summary_enabled" in request:
                config.daily_summary_enabled = request["daily_summary_enabled"]
            if "weekly_report_enabled" in request:
                config.weekly_report_enabled = request["weekly_report_enabled"]
                
        db.commit()
        return {"status": "success", "message": "Notification preferences updated successfully!"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")
