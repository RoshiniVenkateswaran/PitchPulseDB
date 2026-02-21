import json
import logging
import os
from dotenv import load_dotenv

load_dotenv()

from backend.ai.embeddings import embed_text, create_player_week_document
from backend.ai.action_plan import generate_action_plan
from backend.ai.match_report import generate_match_report
# from backend.ai.movement_analysis import analyze_movement 

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def test_embeddings():
    logger.info("=== Testing Embeddings ===")
    
    doc = create_player_week_document(
        player_name="Jude Bellingham",
        week_start="2023-10-23",
        risk_score=72.5,
        readiness=45.0,
        acwr=1.65,
        monotony=2.1,
        strain=3.4,
        last_match_minutes=90,
        drivers=["High ACWR spike", "3 consecutive 90min matches"],
        recommended_action="Cap training minutes, monitor hamstring."
    )
    
    logger.info(f"Canonical Doc:\n{doc}")
    
    vec = embed_text(doc)
    logger.info(f"Embedding generated. Dimension: {len(vec)}")
    logger.info("Embedding Test: PASSED\n")

def test_action_plan():
    logger.info("=== Testing Action Plan ===")
    
    player_context = {
        "name": "Vinicius Jr",
        "position": "Winger",
        "metrics_this_week": {
             "risk_score": 85,
             "readiness_score": 35,
             "drivers": ["Sprint distance +25% vs baseline", "Low sleep quality reported"]
        },
        "last_match": {
            "minutes": 95,
            "high_speed_running_m": 1200
        }
    }
    
    retrieved_cases = [
        {
            "context_data": {"risk_score": 82, "drivers": ["Sprint distance +20%"]},
            "outcome": "Player suffered Grade 1 hamstring strain next match. Recommendation in hindsight: Cap sprint distance in training."
        }
    ]
    
    retrieved_playbook = [
        "Winger Protocol: If Sprint Distance exceeds baseline by 20%+, limit subsequent Match Day -2 technical drills."
    ]
    
    plan = generate_action_plan(player_context, retrieved_cases, retrieved_playbook)
    logger.info(f"Generated Action Plan JSON:\n{json.dumps(plan, indent=2)}")
    logger.info("Action Plan Test: PASSED\n")
    
def test_match_report():
    logger.info("=== Testing Match Report ===")
    
    fixture = {
        "opponent": "Barcelona",
        "result": "Real Madrid 2 - 1 Barcelona",
        "intensity_rating": "Very High"
    }
    
    team_stats = {
        "total_distance_km": 115,
        "avg_possession": "45%"
    }
    
    player_load = [
        {"name": "Valverde", "minutes": 90, "load_flag": "High (ACWR approaching 1.5)"},
        {"name": "Modric", "minutes": 65, "load_flag": "Normal"}
    ]
    
    report = generate_match_report(fixture, team_stats, player_load)
    logger.info(f"Generated Match Report JSON:\n{json.dumps(report, indent=2)}")
    logger.info("Match Report Test: PASSED\n")

if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
         logger.warning("No GEMINI_API_KEY found. Skipping real API calls.")
    else:
         test_embeddings()
         test_action_plan()
         test_match_report()
         
         # Optional movement analysis omitted from automated smoke test 
         # because it requires a local video file.
         logger.info("All Text/Embedding Tests Completed Successfully.")
