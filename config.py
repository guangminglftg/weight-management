import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "health.sqlite3"


@dataclass(frozen=True)
class Settings:
    database_path: Path = Path(os.getenv("WEIGHT_DB_PATH", str(DEFAULT_DB_PATH)))
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    host: str = os.getenv("WEIGHT_APP_HOST", "127.0.0.1")
    port: int = int(os.getenv("WEIGHT_APP_PORT", "7862"))


def get_settings() -> Settings:
    return Settings()
