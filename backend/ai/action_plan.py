import json
from typing import Dict, Any

from .gemini_client import generate_json


def get_action_plan_prompts() -> tuple[str, str]:
    """Retrieves the system and user prompts for action plan generation."""
    import os

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompts_dir = os.path.join(base_dir, "prompts")

    with open(os.path.join(prompts_dir, "action_plan_system.txt"), "r") as f:
         system_prompt = f.read()

    with open(os.path.join(prompts_dir, "action_plan_user.txt"), "r") as f:
         user_prompt_template = f.read()

    return system_prompt, user_prompt_template


def generate_action_plan(player_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a JSON action plan using pure Gemini API.
    Accepts only player_context (name, position, metrics, last match).
    No RAG / Vector DB required.
    """
    # Format context as a readable string for the prompt
    context_str = "CURRENT PLAYER SITUATION:\n"
    context_str += json.dumps(player_context, indent=2) + "\n"

    # Get prompts
    system_prompt, user_prompt_template = get_action_plan_prompts()

    # Format the user prompt
    user_prompt = user_prompt_template.format(context=context_str)

    # Generate structured JSON via Gemini
    return generate_json(system_prompt=system_prompt, user_prompt=user_prompt)
