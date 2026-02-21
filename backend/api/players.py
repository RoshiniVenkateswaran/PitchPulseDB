from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import shutil
import os
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.config import settings
from backend.core.security import get_current_user, User
from backend.models.domain import Player, WeeklyMetric, Fixture, PlayerMatchStat
from backend.services.vector_db import vector_db, get_embedding_safe
from backend.ai.gemini_mock import generate_action_plan_mock
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/{player_id}/detail")
def get_player_detail(player_id: str, weeks: int = 6,
                      current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    cutoff = datetime.utcnow() - timedelta(weeks=weeks)
    metrics = db.query(WeeklyMetric).filter(
        WeeklyMetric.player_id == player_id,
        WeeklyMetric.week_start >= cutoff
    ).order_by(WeeklyMetric.week_start.desc()).all()

    current = metrics[0] if metrics else None

    return {
        "player": player,
        "current_status": {
            "readiness_score": current.readiness_score if current else 0,
            "risk_score": current.risk_score if current else 0,
            "risk_band": current.risk_band if current else "UNKNOWN",
            "acute_load": current.acute_load if current else 0,
            "chronic_load": current.chronic_load if current else 0,
            "acwr": current.acwr if current else 0
        },
        "weekly_history": [
            {
                "week_start": m.week_start,
                "risk_score": m.risk_score,
                "readiness_score": m.readiness_score,
                "acute_load": m.acute_load,
                "acwr": m.acwr
            } for m in metrics
        ]
    }


@router.get("/{player_id}/why")
def get_player_why(player_id: str,
                   current_user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    metric = db.query(WeeklyMetric).filter(
        WeeklyMetric.player_id == player_id
    ).order_by(WeeklyMetric.week_start.desc()).first()
    if not metric:
        return {"drivers": []}
    return {"drivers": metric.drivers_json}


@router.get("/{player_id}/similar_cases")
def get_similar_cases(player_id: str, k: int = 5,
                      current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == player_id).first()
    metric = db.query(WeeklyMetric).filter(
        WeeklyMetric.player_id == player_id
    ).order_by(WeeklyMetric.week_start.desc()).first()

    if not player or not metric:
        return {"cases": []}

    # Build query text using Keerthi's canonical format if possible
    driver_strings = [d.get("factor", "") for d in (metric.drivers_json or [])]
    try:
        from backend.ai.embeddings import create_player_week_document
        query_text = create_player_week_document(
            player_name=player.name,
            week_start=metric.week_start.isoformat() if metric.week_start else "",
            risk_score=metric.risk_score,
            readiness=metric.readiness_score,
            acwr=metric.acwr,
            monotony=metric.monotony,
            strain=metric.strain,
            last_match_minutes=90,  # fallback
            drivers=driver_strings,
            recommended_action=f"Risk {metric.risk_band}"
        )
    except Exception:
        query_text = f"Player {player.name} ACWR {metric.acwr:.2f} risk {metric.risk_band}"

    # Get embedding for query
    query_embedding = get_embedding_safe(query_text)

    results = vector_db.search(query_text=query_text, query_embedding=query_embedding, k=k)
    return {"cases": results}


@router.post("/{player_id}/action_plan")
def action_plan(player_id: str,
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    metric = db.query(WeeklyMetric).filter(
        WeeklyMetric.player_id == player_id
    ).order_by(WeeklyMetric.week_start.desc()).first()

    if not metric:
        return generate_action_plan_mock(player.name, [])

    # Get last match stats
    last_stat = db.query(PlayerMatchStat).filter(
        PlayerMatchStat.player_id == player_id
    ).order_by(PlayerMatchStat.created_at.desc()).first()

    last_match = {}
    if last_stat:
        last_match = {"minutes": last_stat.minutes}
        if last_stat.stats_json:
            last_match.update(last_stat.stats_json)

    # Build player context for Keerthi's action_plan module
    driver_strings = [d.get("factor", "") for d in (metric.drivers_json or [])]
    player_context = {
        "name": player.name,
        "position": player.position or "Unknown",
        "metrics_this_week": {
            "risk_score": metric.risk_score,
            "readiness_score": metric.readiness_score,
            "drivers": driver_strings
        },
        "last_match": last_match
    }

    # Get similar cases from Vector DB for RAG
    query_text = f"Player {player.name} ACWR {metric.acwr:.2f} risk {metric.risk_band}"
    query_embedding = get_embedding_safe(query_text)
    similar_docs = vector_db.search(query_text=query_text, query_embedding=query_embedding, k=3)

    # Format retrieved cases for Keerthi's function signature
    retrieved_cases = []
    for doc in similar_docs:
        if doc.get("metadata", {}).get("source") == "PitchPulse_CaseStudy":
            retrieved_cases.append({
                "context_data": doc.get("metadata", {}),
                "outcome": doc.get("text", "")
            })

    # Get playbook snippets from vector DB
    playbook_query = f"workload management {metric.risk_band} risk protocol"
    playbook_embedding = get_embedding_safe(playbook_query)
    playbook_docs = vector_db.search(query_text=playbook_query, query_embedding=playbook_embedding, k=2)
    retrieved_playbook = [doc.get("text", "") for doc in playbook_docs
                          if doc.get("metadata", {}).get("source") == "PitchPulse_Playbook"]

    # Try Keerthi's real AI module; fall back to mock
    try:
        if settings.GEMINI_API_KEY:
            from backend.ai.action_plan import generate_action_plan
            plan = generate_action_plan(player_context, retrieved_cases, retrieved_playbook)
            return plan
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Real action plan failed, using mock: {e}")

    return generate_action_plan_mock(player.name, similar_docs)

@router.post("/{player_id}/movement_analysis")
def movement_analysis(player_id: str,
                      video: UploadFile = File(...),
                      current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Ensure uploads dir exists
    upload_dir = os.path.join(settings.BASE_DIR if hasattr(settings, 'BASE_DIR') else "/tmp", "temp_uploads")
    os.makedirs(upload_dir, exist_ok=True)
    temp_path = os.path.join(upload_dir, f"{player_id}_{video.filename}")

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        from backend.ai.movement_analysis import analyze_movement
        result = analyze_movement(temp_path, position=player.position)
        return result
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Movement analysis failed: {e}")
        return {
            "mechanical_risk_band": "MED",
            "flags": ["Analysis Failed/Incomplete"],
            "coaching_cues": ["Unable to process video automatically."],
            "confidence": 0.0
        }
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/{player_id}/presage_checkin")
def presage_checkin(player_id: str,
                    body: dict,
                    current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """Process Presage SDK vitals (selfie scan) and return readiness adjustment."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    metric = db.query(WeeklyMetric).filter(
        WeeklyMetric.player_id == player_id
    ).order_by(WeeklyMetric.week_start.desc()).first()

    # Build player context
    player_ctx = {
        "name": player.name,
        "position": player.position or "Unknown",
        "risk_score": metric.risk_score if metric else 0,
        "readiness_score": metric.readiness_score if metric else 0,
        "acwr": metric.acwr if metric else 0,
        "last_match_minutes": 90,
        "baselines": {"resting_hr": 65, "hrv_baseline": 60}
    }

    vitals = body.get("vitals", {})

    try:
        from backend.ai.presage_readiness import process_presage_checkin
        result = process_presage_checkin(player_ctx, vitals)
        return result
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Presage check-in failed: {e}")
        return {
            "readiness_delta": 0,
            "readiness_flag": "OK",
            "emotional_state": "Unknown",
            "contributing_factors": ["Analysis unavailable."],
            "recommendation": "Unable to process vitals. Proceed with normal training."
        }
