import json
from typing import Dict, Any, List

from .gemini_client import generate_json

def get_match_report_prompts() -> tuple[str, str]:
    """Retrieves the system and user prompts for match report generation."""
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompts_dir = os.path.join(base_dir, "prompts")
    
    with open(os.path.join(prompts_dir, "match_report_system.txt"), "r") as f:
         system_prompt = f.read()

    with open(os.path.join(prompts_dir, "match_report_user.txt"), "r") as f:
         user_prompt_template = f.read()
         
    return system_prompt, user_prompt_template

def generate_match_report(fixture_context: Dict[str, Any], 
                          team_stats: Dict[str, Any], 
                          player_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates a high-level JSON match summary focusing on squad workload and
    new risk flags arising from the completed match.
    """
    system_prompt, user_prompt_template = get_match_report_prompts()
    
    # Bundle the context
    context = {
        "fixture": fixture_context,
         # We might only want high level team stats so as not to overwhelm context window
        "team_performance": team_stats,
        "player_loads": player_stats
    }
    
    user_prompt = user_prompt_template.format(context=json.dumps(context, indent=2))
    
    return generate_json(system_prompt=system_prompt, user_prompt=user_prompt)
