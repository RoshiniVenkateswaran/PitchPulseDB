import json
import logging
import os
import time
from typing import Dict, Any, Optional

import google.generativeai as genai
from .movement_flags import build_movement_screen_context

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

def analyze_movement(video_path: str, position: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyzes a short video clip (e.g. 10s squat/hinge) to identify mechanical risks.
    Outputs a strict JSON risk band, flags, and corrective cues grounded in
    soccer-specific biomechanical flag vocabulary.
    
    Args:
        video_path: Local path to the video file (saved by Roshini's upload endpoint).
        position: Optional player position (e.g. "Winger") to focus the analysis on
                  the most relevant soccer-specific flags for that role.

    Returns:
        dict: {
            "mechanical_risk_band": "LOW|MED|HIGH",
            "flags": [...],
            "coaching_cues": [...],
            "confidence": 0.0-1.0
        }
    """
    base_system_prompt, user_prompt = get_movement_prompts()
    
    # Inject position-specific flag context if a position is provided
    if position:
        position_context = build_movement_screen_context(position)
        system_prompt = f"{base_system_prompt}\n\n{position_context}"
        logger.info(f"Position-specific movement context injected for: {position}")
    else:
        system_prompt = base_system_prompt
    
    try:
        logger.info(f"Uploading video {video_path} to Gemini...")
        video_file = genai.upload_file(video_path)
        
        # Wait for the file to be processed by Gemini's video pipeline
        while video_file.state.name == "PROCESSING":
            logger.info("Waiting for Gemini video processing...")
            time.sleep(2)
            video_file = genai.get_file(video_file.name)
            
        if video_file.state.name == "FAILED":
            raise ValueError("Video processing failed on Gemini servers.")
            
        logger.info("Video ready. Generating movement analysis...")
        model = genai.GenerativeModel(
            model_name="gemini-2.5-pro",
            system_instruction=system_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                response_mime_type="application/json",
            )
        )
        
        response = model.generate_content([video_file, user_prompt])
        
        response_text = response.text.strip()
        
        # Defensive strip of markdown if the model hallucinates fences
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            if len(lines) >= 2:
                response_text = "\n".join(lines[1:-1]).strip()
        
        return json.loads(response_text)
        
    except Exception as e:
        logger.error(f"Movement analysis failed: {e}")
        # Return a safe, conservative MED fallback so the app doesn't crash
        return {
            "mechanical_risk_band": "MED",
            "flags": ["Analysis Failed/Incomplete — Manual review required"],
            "coaching_cues": ["Unable to process video automatically. Schedule a physio assessment."],
            "confidence": 0.0
        }
