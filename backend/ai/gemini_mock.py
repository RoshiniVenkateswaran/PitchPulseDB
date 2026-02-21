from typing import Callable

# This serves as a stub for Keerthi's AI layer.
# It defines an exact JSON response to pass back to the app, simulating the Gemini output.

def generate_action_plan_mock(player_name: str, recent_docs: list) -> dict:
    return {
        "summary": f"{player_name} is at high risk due to acute load spike.",
        "why": [
            "ACWR is 1.6 (Dangerous Zone)",
            "Played 270 minutes in 7 days"
        ],
        "recommendations": [
            "Rest for the upcoming cup fixture.",
            "Limit training to recovery protocols only."
        ],
        "caution": "Do not clear for high-speed running drills until day 4."
    }
