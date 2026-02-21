from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "PitchPulse API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database Settings
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/pitchpulse"
    
    # Firebase Settings
    FIREBASE_PROJECT_ID: str = "pitchpulse-demo"
    FIREBASE_KEY_PATH: Optional[str] = None
    
    # Provider Settings
    PROVIDER_API_KEY: Optional[str] = "demo-key"
    USE_DEMO_DATA: bool = True
    
    # Vector DB Settings
    VECTOR_DB_URL: Optional[str] = "http://localhost:8000/vector" # Adjust based on Actian connection
    VECTOR_DB_TOKEN: Optional[str] = None
    
    # Gemini AI Settings
    GEMINI_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
