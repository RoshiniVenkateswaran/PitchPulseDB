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
- Face Detected: {vitals.get('face_detected', 'true')}
- Pulse Rate: {vitals.get('pulse_rate', 'N/A')} bpm
- HRV: {vitals.get('hrv_ms', 'N/A')} ms
- Breathing Rate: {vitals.get('breathing_rate', 'N/A')} breaths/min
- Stress Level: {vitals.get('stress_level', 'N/A')}
- Focus: {vitals.get('focus', 'N/A')}
- Valence: {vitals.get('valence', 'N/A')}
- Confidence: {vitals.get('confidence', 'N/A')}

RULES:
1. If "Face Detected" is false or "no", immediately return:
   readiness_flag: "ALERT", readiness_delta: 0, emotional_state: "No face detected", recommendation: "Please retake the selfie scan."
2. If the data indicates positive/high energy (e.g. happy, active, high valence, normal stress), provide a positive readiness_delta (e.g., +5 to +10) and flag "OK".
3. If the data indicates negative/low energy (e.g. sad, dull, high stress, low valence), provide a negative readiness_delta (e.g., -5 to -15) and flag "CAUTION" or "ALERT".
4. The emotional_state should be a descriptive word (e.g., "Active", "Dull", "Happy", "Sad", "Stressed", "Calm").

Respond ONLY with valid JSON:
{{
  "readiness_delta": <integer, how much to adjust readiness score, e.g. -15 or +5>,
  "readiness_flag": "<OK | CAUTION | ALERT>",
  "emotional_state": "<Active | Dull | Happy | Sad | Stressed | Calm | No face detected>",
  "contributing_factors": ["<factor 1>", "<factor 2>"],
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
    # Check for face detection explicitly
    face_detected = vitals.get("face_detected", True)
    if str(face_detected).lower() in ("false", "no", "0"):
        return {
            "readiness_delta": 0,
            "readiness_flag": "ALERT",
            "emotional_state": "No face detected",
            "contributing_factors": ["Scan failed to detect a human face."],
            "recommendation": "Please ensure you are in a well-lit area and retake the scan."
        }

    stress = str(vitals.get("stress_level", "Normal")).lower()
    focus = str(vitals.get("focus", "High")).lower()
    valence = str(vitals.get("valence", "Positive")).lower()
    pulse = vitals.get("pulse_rate", 70)
    hrv = vitals.get("hrv_ms", 60)

    factors = []
    delta = 0
    emotional = "Calm"

    # Evaluate physical markers
    if isinstance(pulse, (int, float)) and pulse > 85:
        factors.append(f"Resting HR elevated at {pulse}bpm.")
        delta -= 5
    if isinstance(hrv, (int, float)) and hrv < 45:
        factors.append(f"HRV suppressed at {hrv}ms.")
        delta -= 5

    # Evaluate emotional markers strongly
    if valence == "positive" and stress == "normal":
        if focus == "high":
            emotional = "Active"
            delta += 10
            factors.append("High focus and positive valence detected. Optimal state.")
        else:
            emotional = "Happy"
            delta += 5
            factors.append("Positive emotional state detected.")
    elif valence == "negative" or stress in ("high", "very high"):
        if focus == "low":
            emotional = "Dull"
            delta -= 10
            factors.append("Low focus and negative valence detected. Reduced cognitive readiness.")
        else:
            emotional = "Sad" # Or stressed
            delta -= 8
            factors.append("Negative emotional state or high stress detected.")

    if not factors:
        factors = ["All vitals within normal range."]
        delta = 0

    if delta <= -8:
        flag = "ALERT" if stress in ("high", "very high") else "CAUTION"
        rec = "Consider reducing training intensity today to allow for mental and physical recovery."
    elif delta < 0:
        flag = "CAUTION"
        rec = "Monitor closely during the session; player may be fatigued or distracted."
    else:
        flag = "OK"
        rec = "Player is clear for full training load. State is optimal."

    return {
        "readiness_delta": delta,
        "readiness_flag": flag,
        "emotional_state": emotional,
        "contributing_factors": factors,
        "recommendation": rec
    }
