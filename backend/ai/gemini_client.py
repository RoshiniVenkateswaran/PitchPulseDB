import json
import logging
import os
import time
from typing import Any, Dict

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

# Load .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Configure API key (checks environment)
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    logger.warning("GEMINI_API_KEY environment variable not set. Real API calls will fail.")

# Safety settings for conservative outputs
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

def get_model(model_name: str = "gemini-2.5-flash", temperature: float = 0.1) -> genai.GenerativeModel:
    """Returns a configured Gemini model instance."""
    return genai.GenerativeModel(
        model_name=model_name,
        generation_config=genai.types.GenerationConfig(
            temperature=temperature,
            response_mime_type="application/json",
        ),
        safety_settings=SAFETY_SETTINGS,
    )

def _repair_json(bad_json_str: str, error_msg: str, model_name: str = "gemini-2.5-flash") -> Dict[str, Any]:
    """Attempts to repair malformed JSON using the model."""
    logger.info("Attempting to repair malformed JSON...")
    model = get_model(model_name=model_name, temperature=0.0) # Extremely low temp for repair
    prompt = f"""
You are a strict JSON repair utility.
The following string was supposed to be a valid JSON object, but parsing failed with error: {error_msg}

Please fix the errors and output ONLY the valid, repaired JSON object.
Do not include any explanation, markdown formatting (like ```json), or trailing commas.

Malformed JSON:
{bad_json_str}
"""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Remove markdown fences if the model still includes them despite instructions
        if text.startswith("```"):
            lines = text.split("\n")
            if len(lines) >= 2:
                text = "\n".join(lines[1:-1]).strip()
        return json.loads(text)
    except Exception as e:
         logger.error(f"Failed to repair JSON: {e}")
         raise ValueError(f"Could not repair JSON. Original error: {error_msg}")

def generate_json(system_prompt: str, user_prompt: str, model_name: str = "gemini-2.5-flash", max_retries: int = 2) -> Dict[str, Any]:
    """
    Generates content from Gemini and strictly parses it as JSON.
    Includes basic retries and a fallback to an LLM-based JSON repair step.
    """
    model = get_model(model_name=model_name)
    
    # We construct a combined prompt since system instructions are integrated here for simplicity 
    # (though genai handles system_instruction in GenerativeModel optionally, combining is robust).
    # Using the system_instruction parameter:
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.1, # Low temperature for deterministic JSON structure
            response_mime_type="application/json",
        ),
        safety_settings=SAFETY_SETTINGS,
    )

    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            response = model.generate_content(user_prompt)
            # Ensure text exists
            if not response.parts:
                 raise ValueError("Model response was empty (possibly blocked by safety settings).")

            response_text = response.text.strip()
            
            # Defensive markdown strip
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                if len(lines) >= 2:
                    response_text = "\n".join(lines[1:-1]).strip()
            
            return json.loads(response_text)
            
        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(f"JSON decode failed on attempt {attempt + 1}: {e}")
            if attempt < max_retries:
                try:
                     # Attempt LLM repair on the last retry if syntax is just slightly off
                     return _repair_json(response_text, str(e), model_name)
                except Exception as repair_e:
                     logger.warning(f"Repair failed: {repair_e}")
                     time.sleep(1) # Give a brief pause before the next full query retry
                     continue
        except Exception as e:
            last_error = e
            logger.error(f"Generation failed on attempt {attempt + 1}: {e}")
            if attempt < max_retries:
                time.sleep(2)
                continue

    raise ValueError(f"Failed to generate valid JSON after {max_retries + 1} attempts. Last error: {last_error}")

def get_video_model(model_name: str = "gemini-2.5-pro") -> genai.GenerativeModel:
    """Returns a model configured for video/multimodal understanding."""
    return genai.GenerativeModel(
        model_name=model_name,
        generation_config=genai.types.GenerationConfig(
            temperature=0.2, # Slightly higher for nuanced video analysis, but still low
            response_mime_type="application/json",
        ),
        safety_settings=SAFETY_SETTINGS,
    )
