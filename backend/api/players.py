from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import shutil
import os
import logging
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.config import settings
from backend.core.security import get_current_user, User
from backend.models.domain import Player, WeeklyMetric, Fixture, PlayerMatchStat

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{player_id}/detail")
def get_player_detail(player_id: str, weeks: int = 6,
                      current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    from datetime import datetime, timedelta
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
        from backend.ai.gemini_mock import generate_action_plan_mock
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

    # Build player context — simple inputs for Gemini
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

    # Call Gemini directly with player context only (no RAG/Vector DB)
    try:
        if settings.GEMINI_API_KEY:
            from backend.ai.action_plan import generate_action_plan
            plan = generate_action_plan(player_context)
            return plan
    except Exception as e:
        logger.warning(f"Real action plan failed, using mock: {e}")

    from backend.ai.gemini_mock import generate_action_plan_mock
    return generate_action_plan_mock(player.name, [])


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

        # Persist risk band to DB if returned
        if result.get("mechanical_risk_band"):
            wm = db.query(WeeklyMetric).filter(
                WeeklyMetric.player_id == player_id
            ).order_by(WeeklyMetric.week_start.desc()).first()
            if wm:
                wm.risk_band = result["mechanical_risk_band"]
                db.commit()
                logger.info(f"Updated risk_band to {wm.risk_band} for player {player_id}")

        return result
    except Exception as e:
        logger.error(f"Movement analysis failed: {e}")
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


# Default "well-rested" vitals — used when the client sends empty/missing vitals
_HEALTHY_DEFAULT_VITALS = {
    "pulse_rate": 60,
    "hrv_ms": 70,
    "breathing_rate": 14,
    "stress_level": "Normal",
    "focus": "High",
    "valence": "Positive",
    "confidence": 0.9
}


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

    # Use incoming vitals, or fall back to healthy defaults
    vitals = body.get("vitals", {})
    print(f"[Presage RAW VITALS] Player={player.name} Vitals={vitals}", flush=True)

    # ── Detect "No Face" ─────────────────────────────────────────────────────────
    # Prithvi's app sends face_detected: True/False explicitly — trust it directly.
    face_detected = vitals.get("face_detected", True)
    if str(face_detected).lower() in ("false", "0", "no"):
        print(f"[Presage] No face detected for {player.name} — returning ALERT", flush=True)
        return {
            "readiness_delta": 0,
            "readiness_flag": "ALERT",
            "emotional_state": "No face detected",
            "contributing_factors": ["Scan failed to detect a human face."],
            "recommendation": "Please ensure you are in a well-lit area and retake the scan."
        }

    if not vitals or not any(v for k, v in vitals.items() if k != "face_detected"):
        print(f"[Presage] Empty vitals — using healthy defaults for {player.name}", flush=True)
        vitals = _HEALTHY_DEFAULT_VITALS.copy()

    try:
        from backend.ai.presage_readiness import process_presage_checkin
        result = process_presage_checkin(player_ctx, vitals)




        # ── Persist readiness delta to DB ──
        if metric and result.get("readiness_delta") is not None:
            delta = result["readiness_delta"]
            new_readiness = max(0.0, min(100.0, metric.readiness_score + delta))
            new_risk = max(0.0, 100.0 - new_readiness)
            metric.readiness_score = new_readiness
            metric.risk_score = new_risk
            db.commit()
            logger.info(f"[Presage] Updated DB for {player.name}: readiness {new_readiness:.1f} (delta {delta})")

        return result
    except Exception as e:
        logger.error(f"Presage check-in failed: {e}")
        return {
            "readiness_delta": 0,
            "readiness_flag": "OK",
            "emotional_state": "Unknown",
            "contributing_factors": ["Analysis unavailable."],
            "recommendation": "Unable to process vitals. Proceed with normal training."
        }
