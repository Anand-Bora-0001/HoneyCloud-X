from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..deps import get_current_user, get_db
from ...models import InvestigationReport, ThreatCampaign, AttackerProfile, User

router = APIRouter(prefix="/api/investigations", tags=["Investigations"])

@router.get("/")
def get_all_investigations(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == current_user["username"]).first()
    reports = db.query(InvestigationReport).filter(InvestigationReport.organization_id == user.organization_id).order_by(InvestigationReport.updated_at.desc()).all()
    
    return [
        {
            "id": r.id,
            "attacker_id": r.attacker_profile_id,
            "summary": r.executive_summary,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None
        } for r in reports
    ]

@router.get("/{profile_id}")
def get_investigation_details(
    profile_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == current_user["username"]).first()
    report = db.query(InvestigationReport).filter(
        InvestigationReport.attacker_profile_id == profile_id,
        InvestigationReport.organization_id == user.organization_id
    ).first()
    
    if not report:
        # Check if profile exists
        profile = db.query(AttackerProfile).filter(AttackerProfile.id == profile_id, AttackerProfile.organization_id == user.organization_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return {"status": "pending", "message": "Investigation not generated yet"}
        
    import json
    
    def safe_json(val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except:
                pass
        return val

    return {
        "status": "ready",
        "id": report.id,
        "narrative": report.summary_narrative,
        "executive": report.executive_summary,
        "technical": report.technical_summary,
        "mitre_mapping": safe_json(report.mitre_mapping),
        "attack_paths": safe_json(report.attack_paths),
        "risk_evolution": safe_json(report.risk_evolution_trend),
        "evidence": safe_json(report.evidence_summary),
        "updated_at": report.updated_at.isoformat() if report.updated_at else None
    }

@router.get("/campaigns/all")
def get_threat_campaigns(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == current_user["username"]).first()
    campaigns = db.query(ThreatCampaign).filter(ThreatCampaign.organization_id == user.organization_id).order_by(ThreatCampaign.updated_at.desc()).all()
    
    return [
        {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "confidence": c.confidence_score,
            "common_personas": c.common_personas,
            "common_endpoints": c.common_endpoints,
            "common_payloads": c.common_payloads,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        } for c in campaigns
    ]

@router.get("/{profile_id}/report")
def export_investigation_report(
    profile_id: int,
    format: str = "json",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == current_user["username"]).first()
    report = db.query(InvestigationReport).filter(
        InvestigationReport.attacker_profile_id == profile_id,
        InvestigationReport.organization_id == user.organization_id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Investigation not generated yet")
        
    if format == "csv":
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Profile ID", "Executive Summary", "Narrative", "MITRE IDs"])
        writer.writerow([profile_id, report.executive_summary, report.summary_narrative, ",".join(report.mitre_mapping.keys())])
        return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=investigation_{profile_id}.csv"})
        
    return {
        "profile_id": profile_id,
        "executive_summary": report.executive_summary,
        "technical_summary": report.technical_summary,
        "narrative": report.summary_narrative,
        "mitre_mapping": report.mitre_mapping,
        "evidence": report.evidence_summary
    }
