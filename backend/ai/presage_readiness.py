"""
Presage Readiness Check-in Module.
Processes selfie-captured vitals (physical + emotional) to adjust readiness scores.
Uses Gemini AI for analysis with deterministic fallback.
"""

import json
import logging

logger = logging.getLogger(__name__)


def process_presage_checkin(player_context: dict, vitals: dict) -> dict:
    """
    Analyze player vitals from Presage SDK selfie scan and return readiness adjustment.

    Args:
        player_context: dict with keys: name, position, risk_score, readiness_score, acwr, last_match_minutes, baselines
        vitals: dict with keys: pulse_rate, hrv_ms, breathing_rate, stress_level, focus, valence, confidence

    Returns:
        dict with: readiness_delta, readiness_flag, emotional_state, contributing_factors, recommendation
    """
    try:
        from backend.core.config import settings
        if settings.GEMINI_API_KEY:
            return _presage_gemini(player_context, vitals)
    except Exception as e:
        logger.warning(f"Gemini presage check-in failed, using mock: {e}")

    return _presage_mock(player_context, vitals)


def _presage_gemini(player_context: dict, vitals: dict) -> dict:
    """Call Gemini to analyze vitals and return readiness adjustment."""
    from backend.ai.gemini_client import call_gemini

    prompt = f"""You are a sports science AI analyzing pre-training biometric data for a professional footballer.

PLAYER CONTEXT:
- Name: {player_context.get('name', 'Unknown')}
- Position: {player_context.get('position', 'Unknown')}
- Current Risk Score: {player_context.get('risk_score', 'N/A')}
- Current Readiness: {player_context.get('readiness_score', 'N/A')}
- ACWR: {player_context.get('acwr', 'N/A')}

VITALS FROM PRESAGE SDK (selfie scan):
- Pulse Rate: {vitals.get('pulse_rate', 'N/A')} bpm
- HRV: {vitals.get('hrv_ms', 'N/A')} ms
- Breathing Rate: {vitals.get('breathing_rate', 'N/A')} breaths/min
- Stress Level: {vitals.get('stress_level', 'N/A')}
- Focus: {vitals.get('focus', 'N/A')}
- Valence: {vitals.get('valence', 'N/A')}
- Confidence: {vitals.get('confidence', 'N/A')}

Respond ONLY with valid JSON:
{{
  "readiness_delta": <integer, how much to adjust readiness score, e.g. -15 or +5>,
  "readiness_flag": "<OK | CAUTION | ALERT>",
  "emotional_state": "<Calm | Focused | Anxious | Stressed | Fatigued>",
  "contributing_factors": ["<factor 1>", "<factor 2>", "<factor 3>"],
  "recommendation": "<one-sentence coaching recommendation>"
}}"""

    raw = call_gemini(prompt)
    # Parse JSON from response
    try:
        # Strip markdown code fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Failed to parse Gemini presage response, using mock")
        return _presage_mock(player_context, vitals)


def _presage_mock(player_context: dict, vitals: dict) -> dict:
    """Deterministic fallback when Gemini is unavailable."""
    stress = vitals.get("stress_level", "Normal")
    pulse = vitals.get("pulse_rate", 70)
    hrv = vitals.get("hrv_ms", 60)

    factors = []
    delta = 0

    if isinstance(pulse, (int, float)) and pulse > 85:
        factors.append(f"Resting HR elevated at {pulse}bpm (above 80bpm baseline).")
        delta -= 8
    if isinstance(hrv, (int, float)) and hrv < 45:
        factors.append(f"HRV suppressed at {hrv}ms (below 50ms baseline).")
        delta -= 7
    if str(stress).lower() in ("high", "very high"):
        factors.append("High psychological stress detected in facial scan.")
        delta -= 5

    if not factors:
        factors = ["All vitals within normal range."]
        delta = 0

    if delta <= -10:
        flag = "ALERT"
        emotional = "Stressed"
        rec = "Reduce training load and prioritize mental recovery."
    elif delta < 0:
        flag = "CAUTION"
        emotional = "Fatigued"
        rec = "Monitor closely during session; consider lighter drills."
    else:
        flag = "OK"
        emotional = "Calm"
        rec = "Player is cleared for full training."

    return {
        "readiness_delta": delta,
        "readiness_flag": flag,
        "emotional_state": emotional,
        "contributing_factors": factors,
        "recommendation": rec
    }
