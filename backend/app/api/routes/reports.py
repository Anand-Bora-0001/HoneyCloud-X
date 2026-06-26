"""
Report generation and download routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import os
import logging

from ..deps import get_current_user, get_admin_user, get_db
from ...config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.post("/generate")
def generate_report(
    format: str = "csv",
    send_telegram: bool = False,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate attack report in CSV, PDF, or Excel format"""
    try:
        from ...report_generator import generate_csv_report, generate_pdf_report
        from ...excel_export import generate_excel_report
        from .events import attack_events

        # Get stats
        try:
            from .events import get_statistics
            stats = get_statistics(current_user=current_user, db=db)
        except Exception:
            stats = {
                'total_events': 0, 'events_by_service': {},
                'events_by_severity': {}, 'ai_labels': {},
                'last_updated': datetime.now().isoformat()
            }

        # Get events from DB
        try:
            from ...models import AttackEvent, User
            user = db.query(User).filter(User.username == current_user["username"]).first()
            if user:
                db_events = db.query(AttackEvent).filter(
                    AttackEvent.organization_id == user.organization_id,
                    AttackEvent.is_deleted == False
                ).order_by(AttackEvent.timestamp.desc()).limit(limit).all()
                report_events = [{
                    "id": e.id, "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                    "service": e.service_name, "source_ip": e.source_ip,
                    "username": e.username, "password": e.password,
                    "command": e.command, "endpoint": e.endpoint,
                    "method": e.method, "payload": e.payload,
                    "severity": e.severity, "ai_label": e.ai_label,
                    "threat_score": e.threat_score, "location": e.location
                } for e in db_events]
            else:
                report_events = attack_events[:limit]
        except Exception:
            report_events = attack_events[:limit]

        # Trigger background generation
        from ...tasks.report_tasks import generate_report_async
        
        # Check if we should run async or sync
        from ...worker import CELERY_AVAILABLE
        
        if CELERY_AVAILABLE:
            task = generate_report_async.delay(
                report_format=format.lower(),
                events=report_events,
                stats=stats,
                send_telegram=send_telegram,
                organization_id=current_user.get("organization_id")
            )
            return {
                "status": "processing",
                "message": f"{format.upper()} report generation started in background",
                "task_id": task.id,
                "note": "You will receive a notification when the report is ready."
            }
        else:
            # Fallback to sync if worker is not available
            from ...tasks.report_tasks import generate_report_async as sync_gen
            result = sync_gen(
                None,  # self
                report_format=format.lower(),
                events=report_events,
                stats=stats,
                send_telegram=send_telegram,
                organization_id=current_user.get("organization_id")
            )
            
            if result["status"] == "success":
                filepath = result["filepath"]
                return {
                    "status": "success",
                    "message": f"{format.upper()} report generated (sync)",
                    "filepath": filepath,
                    "download_url": f"/api/reports/download?file={os.path.basename(filepath)}"
                }
            else:
                raise Exception(result.get("error", "Unknown error"))

    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download")
def download_report(file: str):
    """Download a generated report file"""
    filepath = os.path.join(settings.reports_dir, file)


    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report file not found")

    media_types = {
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.csv': 'text/csv',
        '.pdf': 'application/pdf'
    }
    ext = os.path.splitext(file)[1]
    media_type = media_types.get(ext, 'application/octet-stream')

    return FileResponse(filepath, media_type=media_type, filename=file)
