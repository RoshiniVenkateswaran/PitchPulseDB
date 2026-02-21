import json
from typing import Dict, Any, List

from .gemini_client import generate_json
from .rag import compose_rag_context

def get_action_plan_prompts() -> tuple[str, str]:
    """Retrieves the system and user prompts for action plan generation."""
    import os
    
    # We load them relative to this file's location to ensure robust imports for FastAPI
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompts_dir = os.path.join(base_dir, "prompts")
    
    with open(os.path.join(prompts_dir, "action_plan_system.txt"), "r") as f:
         system_prompt = f.read()

    with open(os.path.join(prompts_dir, "action_plan_user.txt"), "r") as f:
         user_prompt_template = f.read()
         
    return system_prompt, user_prompt_template

def generate_action_plan(player_context: Dict[str, Any], 
                         retrieved_cases: List[Dict[str, Any]], 
                         retrieved_playbook: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates a deterministic strict JSON action plan for a coach based on a player's latest
    metrics and context retrieved from Actian VectorAI.
    """
    # 1. Compose the context string
    rag_context = compose_rag_context(player_context, retrieved_cases, retrieved_playbook)
    
    # 2. Get prompts
    system_prompt, user_prompt_template = get_action_plan_prompts()
    
    # 3. Format the user prompt
    user_prompt = user_prompt_template.format(context=rag_context)
    
    # 4. Generate the structured JSON response
    # We use a lower temperature because these are actionable performance metrics
    return generate_json(system_prompt=system_prompt, user_prompt=user_prompt)

