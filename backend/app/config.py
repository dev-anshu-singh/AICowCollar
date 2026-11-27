import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    PROJECT_NAME: str = "Smart Cow Collar Telemetry Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # SQLite Database
    DATABASE_PATH: Path = BASE_DIR / "cow_collar.db"
    DATABASE_URL: str = f"sqlite:///{DATABASE_PATH}"
    
    # ML Models Directory
    ML_MODELS_DIR: Path = BASE_DIR / "ml_models"
    MODEL_FILE_PATH: Path = ML_MODELS_DIR / "champion_cow_behavior_model.joblib"
    METADATA_FILE_PATH: Path = ML_MODELS_DIR / "feature_metadata.json"

    # LLM Vet Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

settings = Settings()
