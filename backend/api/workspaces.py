from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import get_current_user, User
from backend.models.domain import Workspace, Player, Fixture, WeeklyMetric
from backend.schemas.api import RequestAccessRequest, RequestAccessResponse, WorkspaceHomeResponse
import datetime

router = APIRouter()

@router.post("/request_access", response_model=RequestAccessResponse)
def request_access(req: RequestAccessRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if already exists
    existing = db.query(Workspace).filter(Workspace.provider_team_id == req.provider_team_id).first()
    if existing:
        return existing
        
    ws = Workspace(
        provider_team_id=req.provider_team_id,
        team_name="Requested Team", # ideally fetched from provider search
        status="pending",
        requested_by_user_id=current_user.id
    )
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return ws

@router.get("/{workspace_id}/home")
def get_home(workspace_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Not found")
        
    fixtures = db.query(Fixture).filter(Fixture.workspace_id == workspace_id).order_by(Fixture.kickoff.desc()).all()
    next_fixture = next((f for f in fixtures if f.status != "FT"), None)
    recent_fixtures = [f for f in fixtures if f.status == "FT"][:3]
    
    players = db.query(Player).filter(Player.workspace_id == workspace_id).all()
    squad_response = []
    
    for p in players:
        # Get latest weekly metric
        metrics = db.query(WeeklyMetric).filter(WeeklyMetric.player_id == p.id).order_by(WeeklyMetric.week_start.desc()).first()
        rs = metrics.readiness_score if metrics else 0.0
        risk = metrics.risk_score if metrics else 0.0
        rband = metrics.risk_band if metrics else "UNKNOWN"
        drivers = [d["factor"] for d in metrics.drivers_json] if metrics and metrics.drivers_json else []
        
        squad_response.append({
            "player": p,
            "readiness_score": rs,
            "risk_score": risk,
            "risk_band": rband,
            "top_drivers": drivers
        })
        
    return {
        "workspace": ws,
        "next_fixture": next_fixture,
        "recent_fixtures": recent_fixtures,
        "squad": squad_response
    }
