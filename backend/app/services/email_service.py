"""
Gmail Email Alert Service for HoneyCloud
Supports SMTP with TLS, HTML templates, plain text fallback, retry logic, and async execution.
"""
import smtplib
import logging
import asyncio
import time
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from ..config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """Enterprise-grade Email service with retry logic and async executor compatibility"""
    
    def __init__(self):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.username = settings.smtp_username
        self.password = settings.smtp_password
        self.from_email = settings.alert_email_from or settings.smtp_from_email or "alerts@honeycloud.com"
        self.from_name = settings.smtp_from_name or "HoneyCloud Security"
        self.use_tls = settings.smtp_use_tls
        self.max_retries = 3
        self.retry_delay = 2 # base delay in seconds for backoff
        
    def is_configured(self) -> bool:
        """Check if email service is properly configured and enabled"""
        if not settings.email_enabled:
            return False
        return bool(settings.resend_api_key or (self.smtp_server and self.username and self.password))
    
    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Asynchronously send email by running the blocking SMTP/HTTP operations in a thread pool executor.
        """
        if not self.is_configured():
            logger.warning("Email service is not configured or is disabled. Skipping dispatch.")
            return False
            
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self.send_email_sync,
            to_emails,
            subject,
            html_body,
            text_body,
            attachments
        )
        
    def send_via_resend(
        self,
        to_emails: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """Send email via Resend's HTTP API"""
        import requests
        import base64
        
        logger.info(f"Dispatching email via Resend API to {', '.join(to_emails)}")
        
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json"
        }
        
        # Determine sender address
        # Resend free tier/unverified accounts can ONLY send from onboarding@resend.dev
        from_domain = self.from_email.split('@')[-1] if '@' in self.from_email else ''
        if from_domain in ('gmail.com', 'honeycloud.com', 'honeycloud.local', 'example.com', 'test.com', 'startup.com', ''):
            sender = f"{self.from_name} <onboarding@resend.dev>"
        else:
            sender = f"{self.from_name} <{self.from_email}>"
            
        payload = {
            "from": sender,
            "to": to_emails,
            "subject": subject,
            "html": html_body,
            "text": text_body or "This is a HoneyCloud Security notification."
        }
        
        # Attachments handling
        if attachments:
            payload_attachments = []
            for file_path in attachments:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "rb") as f:
                            content_bytes = f.read()
                            encoded_content = base64.b64encode(content_bytes).decode("utf-8")
                        payload_attachments.append({
                            "content": encoded_content,
                            "filename": os.path.basename(file_path)
                        })
                    except Exception as e:
                        logger.error(f"Failed to encode attachment for Resend: {e}")
                else:
                    logger.warning(f"Attachment file not found: {file_path}")
            if payload_attachments:
                payload["attachments"] = payload_attachments
                
        # Send request with retries
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=15)
                if response.status_code in (200, 201):
                    logger.info(f"✅ Email delivered successfully via Resend to {', '.join(to_emails)}")
                    return True
                else:
                    logger.error(f"⚠️ Resend API returned error (Attempt {attempt}/{self.max_retries}): {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"⚠️ Resend HTTP request attempt {attempt} failed: {e}")
                
            if attempt < self.max_retries:
                sleep_time = self.retry_delay ** attempt
                logger.info(f"Backing off for {sleep_time} seconds before retry...")
                time.sleep(sleep_time)
                
        logger.error("❌ Resend delivery failed after maximum retries.")
        return False

    def send_email_sync(
        self,
        to_emails: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Synchronously send email with retry logic and detailed error handling.
        """
        if not to_emails:
            logger.error("No recipient email address provided.")
            return False
            
        if settings.resend_api_key:
            return self.send_via_resend(to_emails, subject, html_body, text_body, attachments)
            
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{self.from_name} <{self.from_email}>"
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = subject
        msg['Date'] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
        
        # Attach plain text fallback
        if text_body:
            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        else:
            msg.attach(MIMEText("This is a HoneyCloud Security notification. Please view in an HTML-capable email client.", 'plain', 'utf-8'))
            
        # Attach HTML body
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        # Attach files if provided
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    try:
                        self._attach_file(msg, file_path)
                    except Exception as e:
                        logger.error(f"Failed to attach file {file_path}: {e}")
                else:
                    logger.warning(f"Attachment file not found: {file_path}")
                    
        # Send with retries and exponential backoff
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Attempting SMTP delivery to {', '.join(to_emails)} (Attempt {attempt}/{self.max_retries})...")
                
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                    if self.use_tls:
                        server.starttls()
                    server.login(self.username, self.password)
                    server.send_message(msg)
                    
                logger.info(f"✅ Email delivered successfully to {', '.join(to_emails)}")
                return True
                
            except Exception as e:
                # Do NOT log the password/secrets in exceptions
                logger.error(f"⚠️ SMTP delivery attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    sleep_time = self.retry_delay ** attempt
                    logger.info(f"Backing off for {sleep_time} seconds before retry...")
                    time.sleep(sleep_time)
                else:
                    logger.error("❌ SMTP delivery failed after maximum retries.")
                    return False
                    
        return False
        
    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """Helper to attach a file to the MIMEMultipart message"""
        with open(file_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            
        encoders.encode_base64(part)
        filename = os.path.basename(file_path)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {filename}'
        )
        msg.attach(part)
        logger.debug(f"Attached file: {filename}")
        
    def send_alert_email(
        self,
        to_emails: List[str],
        alert_type: str,
        event_data: Dict[str, Any],
        pdf_report_path: Optional[str] = None
    ) -> bool:
        """
        Converts sync request to async-compatible and triggers dispatch.
        For backward compatibility, this method runs synchronously or inside an executor.
        """
        # Since this can be called from sync or async, we determine context.
        # To remain safe, we run the email sender in the executor if loop exists, otherwise sync.
        subject = f"🚨 HoneyCloud {alert_type} Threat Detected"
        html_body = self._generate_alert_html(alert_type, event_data)
        text_body = self._generate_alert_text(alert_type, event_data)
        
        attachments = [pdf_report_path] if pdf_report_path else None
        
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                # We are in an active event loop
                asyncio.create_task(self.send_email(to_emails, subject, html_body, text_body, attachments))
                return True
        except RuntimeError:
            pass
            
        return self.send_email_sync(to_emails, subject, html_body, text_body, attachments)

    def _generate_alert_html(self, alert_type: str, event_data: Dict[str, Any]) -> str:
        """Generates professional SOC-style enterprise HTML email template"""
        severity_colors = {
            'CRITICAL': '#ef4444',
            'HIGH': '#f97316',
            'MEDIUM': '#eab308',
            'LOW': '#84cc16'
        }
        
        severity = event_data.get('severity', 'UNKNOWN')
        color = severity_colors.get(severity, '#64748b')
        location = event_data.get('location', {})
        
        # Risk score calculation
        threat_score = event_data.get('threat_score', 0.0)
        if threat_score is None:
            risk_score = 50
        elif threat_score > 1.0:
            risk_score = int(min(100.0, threat_score))
        else:
            risk_score = int(min(100.0, threat_score * 100))
        
        # Determine MITRE technique based on endpoint / payload
        mitre_tech = "T1595 - Active Scanning"
        if event_data.get('endpoint'):
            endpoint_lower = event_data.get('endpoint', '').lower()
            if ".env" in endpoint_lower or "config" in endpoint_lower:
                mitre_tech = "T1552.001 - Credentials In Files"
            elif "login" in endpoint_lower or "admin" in endpoint_lower:
                mitre_tech = "T1110.001 - Password Guessing"
                
        # Determine Persona
        persona = event_data.get('persona') or "Scanner"
        
        # Dashboard link configuration
        dashboard_url = os.getenv("FRONTEND_URL", "http://127.0.0.1:8000") + "/dashboard"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>HoneyCloud Security Alert</title>
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #1e293b; max-width: 650px; margin: 0 auto; padding: 0; background-color: #0f172a;">
            
            <!-- Container Wrapper -->
            <div style="background-color: #0f172a; padding: 20px;">
                
                <!-- Main Card -->
                <div style="background-color: #1e293b; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -4px rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.05);">
                    
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #38bdf8; padding: 25px 20px; border-bottom: 2px solid {color}; text-align: center;">
                        <h1 style="margin: 0; font-size: 26px; letter-spacing: 1px; font-weight: 800; display: inline-block; vertical-align: middle;">🍯 HoneyCloud</h1>
                        <p style="margin: 5px 0 0 0; color: #94a3b8; font-size: 14px; text-transform: uppercase; letter-spacing: 2px;">Security Operations Center Alert</p>
                    </div>
                    
                    <!-- Alert Title Section -->
                    <div style="background-color: rgba(239, 68, 68, 0.05); padding: 20px; text-align: center; border-bottom: 1px solid rgba(255, 255, 255, 0.03);">
                        <span style="display: inline-block; background-color: {color}; color: #ffffff; padding: 6px 14px; border-radius: 9999px; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;">
                            {severity} Threat Level
                        </span>
                        <h2 style="margin: 0; font-size: 20px; color: #f8fafc; font-weight: 600;">{alert_type}</h2>
                        <p style="margin: 6px 0 0 0; color: #94a3b8; font-size: 13px;">Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    </div>
                    
                    <!-- Alert Info Grid -->
                    <div style="padding: 25px 20px;">
                        
                        <div style="margin-bottom: 20px;">
                            <h3 style="margin: 0 0 10px 0; font-size: 15px; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); padding-bottom: 4px;">🔍 Incident Overview</h3>
                            <table style="width: 100%; border-collapse: collapse; color: #e2e8f0; font-size: 14px;">
                                <tr>
                                    <td style="padding: 8px 0; color: #94a3b8; font-weight: 500; width: 35%;">Risk Score:</td>
                                    <td style="padding: 8px 0; font-weight: 700; color: {color};">{risk_score}/100</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #94a3b8; font-weight: 500;">Attack Type:</td>
                                    <td style="padding: 8px 0; font-weight: 600;">{event_data.get('service', 'Reconnaissance Scan')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #94a3b8; font-weight: 500;">MITRE ATT&CK:</td>
                                    <td style="padding: 8px 0; font-family: monospace; color: #fb7185;">{mitre_tech}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #94a3b8; font-weight: 500;">Persona:</td>
                                    <td style="padding: 8px 0; color: #f472b6; font-weight: 600;">{persona}</td>
                                </tr>
                            </table>
                        </div>
                        
                        <div style="margin-bottom: 20px;">
                            <h3 style="margin: 0 0 10px 0; font-size: 15px; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); padding-bottom: 4px;">🌐 Network Context</h3>
                            <table style="width: 100%; border-collapse: collapse; color: #e2e8f0; font-size: 14px;">
                                <tr>
                                    <td style="padding: 8px 0; color: #94a3b8; font-weight: 500; width: 35%;">Source IP:</td>
                                    <td style="padding: 8px 0; font-family: monospace; font-weight: bold; color: #f8fafc;">{event_data.get('source_ip', 'Unknown')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #94a3b8; font-weight: 500;">Target service:</td>
                                    <td style="padding: 8px 0;">{event_data.get('service', 'Protected Webnode')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #94a3b8; font-weight: 500;">Target Endpoint:</td>
                                    <td style="padding: 8px 0; font-family: monospace; color: #e2e8f0;">{event_data.get('endpoint') or 'N/A'}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #94a3b8; font-weight: 500;">Geo Location:</td>
                                    <td style="padding: 8px 0;">{location.get('flag', '🌍')} {location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; color: #94a3b8; font-weight: 500;">ISP / Provider:</td>
                                    <td style="padding: 8px 0;">{location.get('isp', 'Unknown')}</td>
                                </tr>
                            </table>
                        </div>
                        
                        {f'''<div style="margin-bottom: 20px; background-color: rgba(0, 0, 0, 0.2); padding: 12px; border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.03);">
                            <div style="color: #94a3b8; font-size: 12px; font-weight: bold; text-transform: uppercase; margin-bottom: 4px;">Payload Logged</div>
                            <pre style="margin: 0; color: #e2e8f0; font-family: monospace; font-size: 12px; white-space: pre-wrap; overflow-x: auto;">{event_data.get('command') or event_data.get('payload')}</pre>
                        </div>''' if event_data.get('command') or event_data.get('payload') else ''}
                        
                        <!-- Recommendations -->
                        <div style="margin-bottom: 25px; background-color: rgba(56, 189, 248, 0.03); border-left: 4px solid #38bdf8; padding: 15px; border-radius: 0 8px 8px 0;">
                            <h4 style="margin: 0 0 8px 0; color: #f8fafc; font-size: 14px; font-weight: 600;">🛡️ Recommended Incident Response</h4>
                            <ul style="margin: 0; padding-left: 20px; color: #94a3b8; font-size: 13px;">
                                <li style="margin-bottom: 5px;">Investigate source IP context via HoneyCloud dashboard.</li>
                                <li style="margin-bottom: 5px;">Evaluate deception action logs to examine attacker intent.</li>
                                <li style="margin-bottom: 5px;">Verify if host security configurations block traffic from this source IP.</li>
                                <li>Review the automatically attached incident report.</li>
                            </ul>
                        </div>
                        
                        <!-- CTA Button -->
                        <div style="text-align: center; margin-top: 25px;">
                            <a href="{dashboard_url}" style="display: inline-block; background-color: #38bdf8; color: #0f172a; padding: 12px 30px; font-weight: 700; border-radius: 6px; text-decoration: none; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; transition: background-color 0.2s;">
                                Go to Dashboard
                            </a>
                        </div>
                        
                    </div>
                    
                    <!-- Footer -->
                    <div style="background-color: #0f172a; padding: 20px; text-align: center; font-size: 11px; color: #64748b; border-top: 1px solid rgba(255, 255, 255, 0.03);">
                        <p style="margin: 0;">This email alert was automatically generated by HoneyCloud Threat Detection Engine.</p>
                        <p style="margin: 5px 0 0 0;">&copy; 2026 HoneyCloud Security Services. All rights reserved.</p>
                    </div>
                    
                </div>
                
            </div>
            
        </body>
        </html>
        """
        return html
        
    def _generate_alert_text(self, alert_type: str, event_data: Dict[str, Any]) -> str:
        """Generates plain text fallback copy of alert email"""
        location = event_data.get('location', {})
        threat_score = event_data.get('threat_score', 0.0)
        if threat_score is None:
            risk_score = 50
        elif threat_score > 1.0:
            risk_score = int(min(100.0, threat_score))
        else:
            risk_score = int(min(100.0, threat_score * 100))
        persona = event_data.get('persona') or "Scanner"
        
        text = f"""
HoneyCloud Security Alert
=======================================
Alert Type: {alert_type}
Severity: {event_data.get('severity', 'UNKNOWN')}
Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

Risk Score: {risk_score}/100
Attack Type: {event_data.get('service', 'Reconnaissance Scan')}
MITRE ATT&CK Mapping: {event_data.get('endpoint', 'Active Scanning')}
Persona: {persona}

Network Context:
-----------------
Source IP: {event_data.get('source_ip', 'Unknown')}
Target Service: {event_data.get('service', 'Protected Webnode')}
Target Endpoint: {event_data.get('endpoint', 'N/A')}
Geo Location: {location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}
ISP: {location.get('isp', 'Unknown')}

Payload Logged:
----------------
{event_data.get('command') or event_data.get('payload') or 'None'}

Recommended Actions:
---------------------
1. Investigate source IP context via HoneyCloud dashboard.
2. Evaluate deception action logs to examine attacker intent.
3. Verify if host security configurations block traffic from this source IP.
4. Review the automatically attached incident report.

This email alert was automatically generated by HoneyCloud Threat Detection Engine.
        """
        return text.strip()

# Global instance
email_service = EmailService()
