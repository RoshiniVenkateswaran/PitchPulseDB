from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta

def calculate_match_load(minutes: int, stats: Dict[str, Any] = None) -> float:
    """
    Computes a simplified match load based on minutes and high-speed running if available.
    """
    base_load = minutes * 5  # arbitrary multiplier for demo
    if stats and "high_speed_running_m" in stats:
        base_load += (stats["high_speed_running_m"] / 100) * 2
    return base_load

def compute_weekly_metrics(daily_loads: List[float], chronic_avg_per_day: float) -> Tuple[float, float, float]:
    """
    Computes Acute Load, Monotony, and Strain.
    daily_loads: list of 7 floats for the week.
    """
    acute_load = sum(daily_loads)
    import statistics
    try:
        std_dev = statistics.stdev(daily_loads)
        monotony = (acute_load / 7) / std_dev if std_dev > 0 else 0
    except statistics.StatisticsError:
        monotony = 0
    
    strain = acute_load * monotony
    
    # Simple Chronic calculation for demo if chronic is 0
    chronic_load = (chronic_avg_per_day * 28) if chronic_avg_per_day > 0 else (acute_load * 0.8) * 4
    if chronic_load == 0: chronic_load = acute_load # Avoid div/0
    
    acwr = acute_load / (chronic_load / 4) if chronic_load > 0 else 1.0

    return acute_load, chronic_load, acwr, monotony, strain

def determine_risk(acwr: float, monotony: float, strain: float, days_since_match: int) -> Tuple[float, str, List[Dict[str, str]]]:
    """
    Returns risk_score (0-100), risk_band, and drivers.
    """
    score = 20.0 # base risk
    drivers = []

    if acwr > 1.5:
        score += 40
        drivers.append({"factor": "High ACWR", "value": f"{acwr:.2f}", "threshold": "1.50", "impact": "negative"})
    elif acwr < 0.8:
        score += 20
        drivers.append({"factor": "Low ACWR (Under-prepared)", "value": f"{acwr:.2f}", "threshold": "0.80", "impact": "negative"})
    else:
        drivers.append({"factor": "Optimal ACWR", "value": f"{acwr:.2f}", "threshold": "0.8-1.5", "impact": "positive"})

    if days_since_match < 3:
        score += 30
        drivers.append({"factor": "Fatigue (Days Since Match)", "value": f"{days_since_match}", "threshold": "3", "impact": "negative"})
    else:
         drivers.append({"factor": "Recovery Adequate", "value": f"{days_since_match}", "threshold": "3", "impact": "positive"})

    if score > 100: score = 100
    
    if score < 36:
        band = "LOW"
    elif score < 66:
        band = "MED"
    else:
        band = "HIGH"

    return score, band, drivers[:3]

def determine_readiness(risk_score: float) -> float:
    # Inverse relationship for demo
    return max(0.0, 100.0 - risk_score)


def compute_baseline_from_stats(total_minutes: int, appearances: int,
                                 avg_rating: float = None, goals: int = 0,
                                 assists: int = 0) -> tuple:
    """
    Compute baseline readiness and risk from real Football API season stats.
    Returns (readiness_score, risk_score, risk_band, drivers_json).

    Logic:
    - High minutes + many appearances → higher fatigue risk, lower readiness
    - High rating / goals / assists → form boost to readiness
    - Few appearances → low workload but also lower match fitness
    """
    drivers = []

    # ── Workload component (minutes per appearance) ──
    if appearances > 0:
        mins_per_app = total_minutes / appearances
    else:
        mins_per_app = 0

    # Base risk from workload (higher minutes/game = more fatigue)
    if mins_per_app >= 85:
        workload_risk = 35  # heavy starter
        drivers.append({"factor": "Heavy starter workload", "value": f"{mins_per_app:.0f} min/game",
                        "threshold": "85", "impact": "negative"})
    elif mins_per_app >= 60:
        workload_risk = 20
        drivers.append({"factor": "Moderate workload", "value": f"{mins_per_app:.0f} min/game",
                        "threshold": "60", "impact": "neutral"})
    elif appearances > 0:
        workload_risk = 10
        drivers.append({"factor": "Rotation / sub role", "value": f"{mins_per_app:.0f} min/game",
                        "threshold": "60", "impact": "positive"})
    else:
        workload_risk = 15
        drivers.append({"factor": "No appearances", "value": "0", "threshold": "N/A", "impact": "negative"})

    # ── Volume component (total appearances in season) ──
    if appearances >= 30:
        volume_risk = 15
        drivers.append({"factor": "High match volume", "value": str(appearances),
                        "threshold": "30", "impact": "negative"})
    elif appearances >= 15:
        volume_risk = 5
    else:
        volume_risk = 0

    # ── Form boost (reduces risk, increases readiness) ──
    form_bonus = 0
    if avg_rating and avg_rating > 0:
        if avg_rating >= 7.5:
            form_bonus = 15
            drivers.append({"factor": "Excellent form", "value": f"{avg_rating:.1f} avg rating",
                            "threshold": "7.5", "impact": "positive"})
        elif avg_rating >= 7.0:
            form_bonus = 8
            drivers.append({"factor": "Good form", "value": f"{avg_rating:.1f} avg rating",
                            "threshold": "7.0", "impact": "positive"})
        elif avg_rating < 6.5:
            form_bonus = -5
            drivers.append({"factor": "Below-average form", "value": f"{avg_rating:.1f} avg rating",
                            "threshold": "6.5", "impact": "negative"})

    # Goal involvement bonus
    goal_involvement = goals + assists
    if goal_involvement >= 10:
        form_bonus += 5
    elif goal_involvement >= 5:
        form_bonus += 2

    # ── Final calculation ──
    risk_score = max(5.0, min(80.0, float(workload_risk + volume_risk - form_bonus * 0.3)))
    readiness_score = max(20.0, min(95.0, 100.0 - risk_score + form_bonus * 0.5))

    if risk_score >= 50:
        risk_band = "HIGH"
    elif risk_score >= 25:
        risk_band = "MED"
    else:
        risk_band = "LOW"

    return readiness_score, risk_score, risk_band, drivers[:3]

