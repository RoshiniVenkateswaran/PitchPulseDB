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
