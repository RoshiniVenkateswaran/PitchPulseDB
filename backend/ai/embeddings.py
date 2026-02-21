import logging
from typing import List, Dict, Any

from google.generativeai import embed_content

logger = logging.getLogger(__name__)

# Constants
EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_TASK_TYPE = "RETRIEVAL_DOCUMENT"

def embed_text(text: str) -> List[float]:
    """
    Generates text embeddings using Gemini's text-embedding-004 model.
    The resulting vector is suitable for insertion into Actian VectorAI DB.
    """
    try:
        response = embed_content(
            model=EMBEDDING_MODEL,
            content=text,
            task_type=EMBEDDING_TASK_TYPE,
        )
        return response['embedding']
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        # Re-raise so the caller handles the failure (e.g., retrying from the sync worker)
        raise ValueError(f"Embedding generation failed: {e}")

def create_player_week_document(player_name: str, 
                              week_start: str, 
                              risk_score: float, 
                              readiness: float,
                              acwr: float,
                              monotony: float,
                              strain: float,
                              last_match_minutes: float,
                              drivers: List[str],
                              recommended_action: str) -> str:
    """
    Constructs a consistent, canonical string representation of a Player-Week.
    This guarantees that the structural composition of embeddings stays uniform
    across both database ingestions and real-time query retrievals.
    """
    drivers_str = ", ".join(drivers) if drivers else "None"
    
    template = (f"Player {player_name} week {week_start}. "
                f"risk {risk_score} readiness {readiness}. "
                f"ACWR {acwr}. monotony {monotony}. strain {strain}. "
                f"last_match_minutes {last_match_minutes}. "
                f"drivers: {drivers_str}. recommended: {recommended_action}.")
    
    return template.strip()
