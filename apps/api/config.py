"""Application configuration."""

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self) -> None:
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        self.app_name: str = "Pharmacy Agent"
        self.app_version: str = "0.1.0"
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.db_path: str = os.getenv("DB_PATH", "data/pharmacy.db")

        # Fail fast if OPENAI_API_KEY is missing
        if not self.openai_api_key and not self.debug:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Set it in your environment or .env file."
            )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
