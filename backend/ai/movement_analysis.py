import json
import logging
import os
import time
from typing import Dict, Any

from google.generativeai import upload_file, get_file
from .gemini_client import get_video_model

logger = logging.getLogger(__name__)

def get_movement_prompts() -> tuple[str, str]:
    """Retrieves the system and user prompts for movement analysis."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompts_dir = os.path.join(base_dir, "prompts")
    
    with open(os.path.join(prompts_dir, "movement_system.txt"), "r") as f:
         system_prompt = f.read()

    with open(os.path.join(prompts_dir, "movement_user.txt"), "r") as f:
         user_prompt = f.read()
         
    return system_prompt, user_prompt

def analyze_movement(video_path: str) -> Dict[str, Any]:
    """
    Analyzes a short video clip (e.g. 10s squat/hinge) to identify mechanical risks.
    Outputs a strict JSON risk band, flags, and corrective cues.
    
    NOTE: video_path should be a local path accessible to the backend server.
    If receiving a URL, download it locally first before calling this function.
    """
    system_prompt, user_prompt = get_movement_prompts()
    
    try:
        logger.info(f"Uploading video {video_path} to Gemini...")
        video_file = upload_file(video_path)
        
        # Wait for the file to be processed
        while video_file.state.name == "PROCESSING":
            logger.info("Waiting for video processing...")
            time.sleep(2)
            video_file = get_file(video_file.name)
            
        if video_file.state.name == "FAILED":
            raise ValueError(f"Video processing failed on Gemini servers.")
            
        logger.info("Video ready. Initializing model for analysis.")
        # Add system context
        model = get_video_model()
        model._system_instruction = system_prompt # Ensure it takes hold when calling generate
        
        response = model.generate_content(
            [video_file, user_prompt]
        )
        
        response_text = response.text.strip()
        
        # Defensive strip of markdown if the model hallucinates it
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            if len(lines) >= 2:
                response_text = "\n".join(lines[1:-1]).strip()
        
        return json.loads(response_text)
        
    except Exception as e:
        logger.error(f"Movement analysis failed: {e}")
        # Return a safe, conservative fallback
        return {
            "mechanical_risk_band": "MED",
            "flags": ["Analysis Failed/Incomplete"],
            "coaching_cues": ["Unable to process video automatically, manual review required."],
            "confidence": 0.0
        }
