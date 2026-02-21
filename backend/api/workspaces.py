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


@router.post("/{workspace_id}/suggested-xi")
def suggested_xi(workspace_id: str,
                 body: dict,
                 current_user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """Generate AI-recommended Starting XI based on squad readiness and opponent."""
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    opponent = body.get("opponent", "Unknown")
    match_context = body.get("match_context", "")

    # If client sent available_squad, use it directly; otherwise build from DB
    available_squad = body.get("available_squad")
    if not available_squad:
        players = db.query(Player).filter(Player.workspace_id == workspace_id).all()
        available_squad = []
        for p in players:
            metric = db.query(WeeklyMetric).filter(
                WeeklyMetric.player_id == p.id
            ).order_by(WeeklyMetric.week_start.desc()).first()
            available_squad.append({
                "id": str(p.id),
                "name": p.name,
                "position": p.position or "Unknown",
                "readiness": metric.readiness_score if metric else 50,
                "form": "Good" if (metric and metric.readiness_score > 70) else "Average"
            })

    try:
        from backend.ai.suggested_xi import generate_suggested_xi
        result = generate_suggested_xi(opponent, match_context, available_squad)
        return result
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Suggested XI failed: {e}")
        return {
            "best_formation": "4-3-3",
            "tactical_analysis": "Default formation selected due to analysis unavailability.",
            "starting_xi_ids": [str(s["id"]) for s in available_squad[:11]],
            "bench_ids": [str(s["id"]) for s in available_squad[11:]],
            "player_rationales": {}
        }
