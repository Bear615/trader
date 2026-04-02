from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    admin_api_key: str = "change-me"
    login_pin: str = ""   # Set LOGIN_PIN in .env — users enter this to access the site
    db_path: str = "./trading.db"
    poll_interval_seconds: int = 10
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    ollama_base_url: str = "http://localhost:11434/api"  # override via OLLAMA_BASE_URL in .env

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


config = Config()
