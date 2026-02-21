from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import json

from backend.core.database import get_db
from backend.core.config import settings
from backend.models.domain import Workspace, Player, Fixture, PlayerMatchStat, DailyLoad, WeeklyMetric, MatchReport
from backend.schemas.api import SyncResponse
from backend.services.provider import provider
from backend.services.metrics import calculate_match_load, compute_weekly_metrics, determine_risk, determine_readiness
from backend.services.vector_db import vector_db, get_embedding_safe

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/workspace/{workspace_id}/initial", response_model=SyncResponse)
def sync_workspace_initial(workspace_id: str, use_demo: bool = True, db: Session = Depends(get_db)):
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Get Squad
    squad_data = provider.get_squad(workspace.provider_team_id)
    players_added = 0
    for p_data in squad_data:
        existing = db.query(Player).filter(
            Player.provider_player_id == p_data["provider_player_id"],
            Player.workspace_id == workspace.id
        ).first()
        if not existing:
            new_player = Player(
                workspace_id=workspace.id,
                provider_player_id=p_data["provider_player_id"],
                name=p_data["name"],
                position=p_data.get("position"),
                jersey=p_data.get("jersey")
            )
            db.add(new_player)
            db.flush()  # get ID assigned

            # Init empty weekly metric
            wm = WeeklyMetric(
                player_id=new_player.id,
                week_start=datetime.utcnow() - timedelta(days=datetime.utcnow().weekday()),
                risk_score=20.0,
                readiness_score=80.0,
                risk_band="LOW",
                drivers_json=[{"factor": "Baseline", "value": "N/A", "threshold": "N/A", "impact": "positive"}]
            )
            db.add(wm)
            players_added += 1

    # Get Fixtures
    fixtures_data = provider.get_fixtures(workspace.provider_team_id, "2023-10-01", "2023-11-01")
    fixtures_added = 0
    for f_data in fixtures_data:
        existing = db.query(Fixture).filter(
            Fixture.provider_fixture_id == f_data["provider_fixture_id"],
            Fixture.workspace_id == workspace.id
        ).first()
        if not existing:
            new_fixture = Fixture(
                workspace_id=workspace.id,
                provider_fixture_id=f_data["provider_fixture_id"],
                kickoff=datetime.fromisoformat(f_data["kickoff"].replace('Z', '+00:00')),
                opponent_name=f_data["opponent_name"],
                home_away=f_data["home_away"],
                status=f_data["status"],
                score_home=f_data.get("score_home"),
                score_away=f_data.get("score_away")
            )
            db.add(new_fixture)
            fixtures_added += 1

    db.commit()
    return SyncResponse(status="success", players_synced=players_added, fixtures_synced=fixtures_added)


@router.post("/fixtures/poll_once", response_model=SyncResponse)
def sync_fixtures_poll(use_demo: bool = True, db: Session = Depends(get_db)):
    """
    Polling worker simulation. Finds un-synced FT fixtures and processes their stats.
    After processing:
      1. Computes match loads → daily_load
      2. Recomputes weekly_metrics for involved players
      3. Generates match report via Keerthi's AI module
      4. Upserts player-week embeddings into VectorAI DB
    """
    fixtures = db.query(Fixture).filter(Fixture.status == "FT", Fixture.last_synced_at == None).all()

    fixtures_processed = 0
    stats_ingested = 0
    player_stats_for_report = []  # Collect for match report generation

    for fixture in fixtures:
        stats_data = provider.get_fixture_player_stats(fixture.provider_fixture_id)
        if not stats_data:
            continue

        player_stats_for_report = []

        for s_data in stats_data:
            player = db.query(Player).filter(
                Player.provider_player_id == s_data["provider_player_id"]
            ).first()
            if not player:
                continue

            match_load = calculate_match_load(s_data["minutes"], s_data.get("stats_json"))

            # Insert player match stat
            pms = PlayerMatchStat(
                fixture_id=fixture.id,
                player_id=player.id,
                minutes=s_data["minutes"],
                stats_json=s_data.get("stats_json", {})
            )
            db.add(pms)

            # Insert daily load
            dl = DailyLoad(
                player_id=player.id,
                date=fixture.kickoff,
                source="match",
                load_value=match_load
            )
            db.add(dl)
            stats_ingested += 1

            # Recalculate Weekly Metrics
            mock_daily = [40, 50, 0, 80, 0, 30, match_load]
            acute, chronic, acwr, monotony, strain = compute_weekly_metrics(mock_daily, 60.0)

            days_since = max(0, (datetime.utcnow().replace(tzinfo=None) -
                                 fixture.kickoff.replace(tzinfo=None)).days)

            risk_score, risk_band, drivers = determine_risk(acwr, monotony, strain, days_since)
            readiness = determine_readiness(risk_score)

            # Update latest weekly metric
            week_start = fixture.kickoff - timedelta(days=fixture.kickoff.weekday())
            wm = db.query(WeeklyMetric).filter(
                WeeklyMetric.player_id == player.id
            ).order_by(WeeklyMetric.week_start.desc()).first()
            if not wm:
                wm = WeeklyMetric(player_id=player.id, week_start=week_start)
                db.add(wm)

            wm.acute_load = acute
            wm.chronic_load = chronic
            wm.acwr = acwr
            wm.monotony = monotony
            wm.strain = strain
            wm.risk_score = risk_score
            wm.risk_band = risk_band
            wm.readiness_score = readiness
            wm.drivers_json = drivers

            # --- VECTOR DB: Build canonical doc + embed + upsert ---
            driver_strings = [d["factor"] for d in drivers]
            try:
                from backend.ai.embeddings import create_player_week_document
                doc_text = create_player_week_document(
                    player_name=player.name,
                    week_start=week_start.isoformat(),
                    risk_score=risk_score,
                    readiness=readiness,
                    acwr=acwr,
                    monotony=monotony,
                    strain=strain,
                    last_match_minutes=s_data["minutes"],
                    drivers=driver_strings,
                    recommended_action=f"Risk {risk_band}: manage load accordingly."
                )
            except Exception:
                doc_text = (f"{player.name} week {week_start.isoformat()} ACWR {acwr:.2f} "
                            f"Risk {risk_band}. Drivers: {driver_strings}")

            embedding = get_embedding_safe(doc_text)
            doc_id = f"week_{player.id}_{week_start.isoformat()}"
            vector_db.upsert(
                doc_id=doc_id,
                text=doc_text,
                embedding=embedding,
                metadata={"player_id": player.id, "week": week_start.isoformat(), "acwr": acwr}
            )

            # Collect for match report
            load_flag = f"{'High' if risk_band == 'HIGH' else 'Normal'} (ACWR {acwr:.2f})"
            player_stats_for_report.append({
                "name": player.name,
                "minutes": s_data["minutes"],
                "load_flag": load_flag
            })

        # --- MATCH REPORT: Generate via Keerthi's AI module ---
        fixture_context = {
            "opponent": fixture.opponent_name,
            "result": f"{fixture.score_home} - {fixture.score_away}",
            "intensity_rating": "High"
        }
        team_stats = {"total_distance_km": 110, "avg_possession": "52%"}  # mock team-level

        try:
            if settings.GEMINI_API_KEY:
                from backend.ai.match_report import generate_match_report
                report_json = generate_match_report(fixture_context, team_stats, player_stats_for_report)
            else:
                report_json = {
                    "match_summary": f"Match vs {fixture.opponent_name} ended {fixture.score_home}-{fixture.score_away}.",
                    "squad_load_assessment": "Standard fixture load across the squad.",
                    "critical_flags": []
                }
        except Exception as e:
            logger.warning(f"Match report generation failed, using fallback: {e}")
            report_json = {
                "match_summary": f"Match vs {fixture.opponent_name} ended {fixture.score_home}-{fixture.score_away}.",
                "squad_load_assessment": "Unable to generate AI assessment.",
                "critical_flags": [str(e)]
            }

        mr = MatchReport(
            fixture_id=fixture.id,
            workspace_id=fixture.workspace_id,
            report_json=report_json
        )
        db.add(mr)

        # Upsert match report embedding too
        report_text = json.dumps(report_json)
        report_embedding = get_embedding_safe(report_text)
        vector_db.upsert(
            doc_id=f"match_report_{fixture.id}",
            text=report_text,
            embedding=report_embedding,
            metadata={"fixture_id": fixture.id, "type": "match_report"}
        )

        fixture.last_synced_at = datetime.utcnow()
        fixtures_processed += 1

    db.commit()
    return SyncResponse(status="success", fixtures_processed=fixtures_processed, stats_ingested=stats_ingested)
