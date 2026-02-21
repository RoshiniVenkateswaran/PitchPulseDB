from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import get_current_user, User
from backend.models.domain import Workspace, Player, Fixture, WeeklyMetric
from backend.schemas.api import RequestAccessRequest, RequestAccessResponse, WorkspaceHomeResponse
from backend.services.provider import provider
from backend.services.metrics import compute_weekly_metrics, determine_risk, determine_readiness
import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def _run_initial_sync(workspace_id: str, provider_team_id: int, db: Session):
    """Fetch squad + fixtures immediately after workspace creation."""
    try:
        # Import sync logic inline to avoid circular imports
        from backend.api.sync import sync_workspace_initial
        sync_workspace_initial(workspace_id=workspace_id, use_demo=True, db=db)
        logger.info(f"Auto-sync complete for workspace {workspace_id}")
    except Exception as e:
        logger.error(f"Auto-sync failed for workspace {workspace_id}: {e}")


@router.post("/request_access", response_model=RequestAccessResponse)
def request_access(req: RequestAccessRequest,
                   background_tasks: BackgroundTasks,
                   current_user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """
    Club selection: auto-approves workspace and immediately triggers data sync.
    No admin approval needed.
    """
    # Check if this user already has a workspace for this team
    existing = db.query(Workspace).filter(
        Workspace.provider_team_id == req.provider_team_id,
        Workspace.requested_by_user_id == current_user.id
    ).first()
    if existing:
        return existing

    # Look up team name from the provider
    search_results = provider.search_clubs(str(req.provider_team_id))
    team_name = search_results[0]["name"] if search_results else f"Team {req.provider_team_id}"

    # Create workspace already approved — no waiting
    ws = Workspace(
        provider_team_id=req.provider_team_id,
        team_name=team_name,
        status="approved",
        requested_by_user_id=current_user.id
    )
    db.add(ws)
    db.commit()
    db.refresh(ws)

    # Trigger squad + fixtures sync in the background so the response is instant
    background_tasks.add_task(_run_initial_sync, str(ws.id), req.provider_team_id, db)

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
