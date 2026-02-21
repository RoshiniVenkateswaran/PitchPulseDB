import json
from typing import List, Dict, Any

def compose_rag_context(player_context: Dict[str, Any], retrieved_cases: List[Dict[str, Any]], retrieved_playbook: List[Dict[str, Any]]) -> str:
    """
    Composes a string combining the player's current context with similar historical
    cases and specific playbook snippets retrieved from Actian VectorAI DB.
    """
    # 1. Format the current player context
    context_str = "CURRENT PLAYER SITUATION:\n"
    context_str += json.dumps(player_context, indent=2) + "\n\n"
    
    # 2. Format similar cases
    context_str += "SIMILAR HISTORICAL CASES (FROM VECTOR DB):\n"
    if not retrieved_cases:
        context_str += "No strongly matching similar cases found.\n"
    else:
        for idx, case in enumerate(retrieved_cases, 1):
            context_str += f"Case {idx}:\n"
            # Explicitly format what the case was and what the outcome was
            context_str += f"- Context: {json.dumps(case.get('context_data', {}))}\n"
            context_str += f"- Subsequent Intervention/Outcome: {case.get('outcome', 'Unknown')}\n"
    context_str += "\n"

    # 3. Format Playbook Guidance
    context_str += "CLUB PLAYBOOK GUIDELINES (FROM VECTOR DB):\n"
    if not retrieved_playbook:
        context_str += "No specific playbook guidance retrieved.\n"
    else:
        for snippet in retrieved_playbook:
            if isinstance(snippet, dict):
                context_str += f"- {snippet.get('rule_text', 'No rule text')}\n"
            else:
                context_str += f"- {snippet}\n"
            
    return context_str
