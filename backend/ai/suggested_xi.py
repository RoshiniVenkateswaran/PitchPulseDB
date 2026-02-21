"""
Suggested XI Module.
Generates AI-recommended tactical formations and Starting XI based on squad readiness.
Uses Gemini AI for analysis with deterministic fallback.
"""

import json
import logging

logger = logging.getLogger(__name__)


def generate_suggested_xi(opponent: str, match_context: str, available_squad: list) -> dict:
    """
    Generate an AI-recommended Starting XI and formation.

    Args:
        opponent: Name of the opposing team
        match_context: e.g. "Away, Champions League Semi-Final"
        available_squad: list of dicts with keys: id, name, position, readiness, form

    Returns:
        dict with: best_formation, tactical_analysis, starting_xi_ids, bench_ids, player_rationales
    """
    try:
        from backend.core.config import settings
        if settings.GEMINI_API_KEY:
            return _suggested_xi_gemini(opponent, match_context, available_squad)
    except Exception as e:
        logger.warning(f"Gemini suggested XI failed, using mock: {e}")

    return _suggested_xi_mock(opponent, match_context, available_squad)


def _suggested_xi_gemini(opponent: str, match_context: str, available_squad: list) -> dict:
    """Call Gemini to generate tactical formation and XI."""
    from backend.ai.gemini_client import call_gemini

    squad_text = "\n".join(
        f"  - ID: {p['id']}, Name: {p['name']}, Pos: {p['position']}, "
        f"Readiness: {p.get('readiness', 'N/A')}%, Form: {p.get('form', 'N/A')}"
        for p in available_squad
    )

    prompt = f"""You are an elite football tactical AI assistant for a professional club.

MATCH INFO:
- Opponent: {opponent}
- Context: {match_context}

AVAILABLE SQUAD:
{squad_text}

Select the best formation and Starting XI (11 players) based on readiness scores, positions, and form.
Place remaining players on the bench.

Respond ONLY with valid JSON:
{{
  "best_formation": "<e.g. 4-3-3>",
  "tactical_analysis": "<2-3 sentence analysis of why this formation was chosen>",
  "starting_xi_ids": ["<id1>", "<id2>", ... up to 11 player IDs],
  "bench_ids": ["<id1>", "<id2>", ...],
  "player_rationales": {{
    "<player_id>": "<1 sentence rationale for inclusion/exclusion>"
  }}
}}"""

    raw = call_gemini(prompt)
    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Failed to parse Gemini suggested XI response, using mock")
        return _suggested_xi_mock(opponent, match_context, available_squad)


def _suggested_xi_mock(opponent: str, match_context: str, available_squad: list) -> dict:
    """Deterministic fallback when Gemini is unavailable."""
    # Sort by readiness (highest first), then pick top 11 for starting XI
    sorted_squad = sorted(
        available_squad,
        key=lambda p: p.get("readiness", 0),
        reverse=True
    )

    starting = sorted_squad[:11]
    bench = sorted_squad[11:]

    starting_ids = [str(p["id"]) for p in starting]
    bench_ids = [str(p["id"]) for p in bench]

    rationales = {}
    for p in starting:
        rationales[str(p["id"])] = (
            f"{p['name']} selected — {p.get('readiness', 'N/A')}% readiness, "
            f"form: {p.get('form', 'N/A')}."
        )
    for p in bench:
        rationales[str(p["id"])] = (
            f"{p['name']} benched — readiness at {p.get('readiness', 'N/A')}%."
        )

    return {
        "best_formation": "4-3-3",
        "tactical_analysis": (
            f"4-3-3 selected to counter {opponent} in a {match_context} scenario. "
            f"Top 11 players by readiness score were chosen to maximize squad fitness."
        ),
        "starting_xi_ids": starting_ids,
        "bench_ids": bench_ids,
        "player_rationales": rationales
    }
