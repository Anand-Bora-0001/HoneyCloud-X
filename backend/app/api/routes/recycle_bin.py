from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ..deps import get_current_user, get_db

router = APIRouter(prefix="/api/recycle-bin", tags=["Recycle Bin"])

@router.get("")
def get_deleted_items(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from ...models import AttackEvent, User, InvestigationReport
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    events = db.query(AttackEvent).filter(AttackEvent.organization_id == user.organization_id, AttackEvent.is_deleted == True).order_by(AttackEvent.deleted_at.desc()).limit(100).all()
    
    items = []
    for e in events:
        items.append({
            "id": e.id,
            "type": "AttackEvent",
            "name": f"Event #{e.id} ({e.service_name})",
            "deleted_at": e.deleted_at.isoformat() if e.deleted_at else None,
            "severity": e.severity,
            "source_ip": e.source_ip
        })
        
    reports = db.query(InvestigationReport).filter(InvestigationReport.organization_id == user.organization_id, InvestigationReport.is_deleted == True).order_by(InvestigationReport.deleted_at.desc()).limit(100).all()
    for r in reports:
        items.append({
            "id": r.id,
            "type": "InvestigationReport",
            "name": f"Investigation #{r.id}",
            "deleted_at": r.deleted_at.isoformat() if r.deleted_at else None,
            "severity": "N/A",
            "source_ip": "Report"
        })
    
    return sorted(items, key=lambda x: x["deleted_at"] or "", reverse=True)

@router.post("/restore")
def restore_items(
    payload: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from ...models import AttackEvent, User, AuditLog, InvestigationReport, AttackerProfile, DeceptionSession
    user = db.query(User).filter(User.username == current_user["username"]).first()
    
    ids = payload.get("ids", [])
    item_type = payload.get("type", "AttackEvent")
    
    restored_count = 0
    if not ids:
        # Bulk restore everything
        restored_count += db.query(AttackEvent).filter(AttackEvent.organization_id == user.organization_id, AttackEvent.is_deleted == True).update({"is_deleted": False, "deleted_at": None}, synchronize_session=False)
        db.query(InvestigationReport).filter(InvestigationReport.organization_id == user.organization_id, InvestigationReport.is_deleted == True).update({"is_deleted": False, "deleted_at": None}, synchronize_session=False)
        db.query(AttackerProfile).filter(AttackerProfile.organization_id == user.organization_id, AttackerProfile.is_deleted == True).update({"is_deleted": False, "deleted_at": None}, synchronize_session=False)
        db.query(DeceptionSession).filter(DeceptionSession.organization_id == user.organization_id, DeceptionSession.is_deleted == True).update({"is_deleted": False, "deleted_at": None}, synchronize_session=False)
    else:
        if item_type == "AttackEvent":
            restored_count = db.query(AttackEvent).filter(AttackEvent.organization_id == user.organization_id, AttackEvent.id.in_(ids)).update({"is_deleted": False, "deleted_at": None}, synchronize_session=False)
        elif item_type == "InvestigationReport":
            restored_count = db.query(InvestigationReport).filter(InvestigationReport.organization_id == user.organization_id, InvestigationReport.id.in_(ids)).update({"is_deleted": False, "deleted_at": None}, synchronize_session=False)

    db.commit()
        
    audit = AuditLog(
        organization_id=user.organization_id,
        user_id=user.id,
        action="Restore Recycle Bin",
        records_removed=0,
        details={"restored_count": restored_count}
    )
    db.add(audit)
    db.commit()
        
    return {"status": "success", "restored": restored_count}

@router.delete("/permanent")
def permanent_delete(
    payload: dict = {},
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from ...models import AttackEvent, User, AuditLog, DeceptionSession, DeceptionAction, AttackerProfile, FileUploadAttempt, InvestigationReport
    user = db.query(User).filter(User.username == current_user["username"]).first()
    
    ids = payload.get("ids", [])
    item_type = payload.get("type", "AttackEvent")
    deleted_count = 0
    
    if ids:
        if item_type == "AttackEvent":
            deleted_count = db.query(AttackEvent).filter(AttackEvent.organization_id == user.organization_id, AttackEvent.id.in_(ids), AttackEvent.is_deleted == True).delete(synchronize_session=False)
        elif item_type == "InvestigationReport":
            deleted_count = db.query(InvestigationReport).filter(InvestigationReport.organization_id == user.organization_id, InvestigationReport.id.in_(ids), InvestigationReport.is_deleted == True).delete(synchronize_session=False)
    else:
        # Empty Recycle Bin completely
        session_ids = [s.session_id for s in db.query(DeceptionSession.session_id).filter(DeceptionSession.organization_id == user.organization_id, DeceptionSession.is_deleted == True).all()]
        if session_ids:
            db.query(DeceptionAction).filter(DeceptionAction.session_id.in_(session_ids)).delete(synchronize_session=False)
            db.query(FileUploadAttempt).filter(FileUploadAttempt.session_id.in_(session_ids)).delete(synchronize_session=False)
            db.query(DeceptionSession).filter(DeceptionSession.session_id.in_(session_ids)).delete(synchronize_session=False)

        profile_ids = [p.id for p in db.query(AttackerProfile.id).filter(AttackerProfile.organization_id == user.organization_id, AttackerProfile.is_deleted == True).all()]
        if profile_ids:
            db.query(InvestigationReport).filter(InvestigationReport.attacker_profile_id.in_(profile_ids)).delete(synchronize_session=False)
            db.query(AttackerProfile).filter(AttackerProfile.id.in_(profile_ids)).delete(synchronize_session=False)

        # Standalone reports
        db.query(InvestigationReport).filter(InvestigationReport.organization_id == user.organization_id, InvestigationReport.is_deleted == True).delete(synchronize_session=False)

        deleted_count = db.query(AttackEvent).filter(AttackEvent.organization_id == user.organization_id, AttackEvent.is_deleted == True).delete(synchronize_session=False)
        
    db.commit()
    
    audit = AuditLog(
        organization_id=user.organization_id,
        user_id=user.id,
        action="Empty Recycle Bin",
        records_removed=deleted_count,
        details={"type": "permanent_delete"}
    )
    db.add(audit)
    db.commit()

    return {"status": "success", "permanently_deleted": deleted_count}
