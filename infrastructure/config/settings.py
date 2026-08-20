"""
AHOS Configuration Settings
Type-safe settings using Pydantic
"""
from pathlib import Path
from typing import Optional, List
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # API Keys (Free Tiers)
    YFINANCE_API_KEY: Optional[str] = None
    COINGECKO_API_KEY: Optional[str] = None
    ALPHAVANTAGE_API_KEY: Optional[str] = Field(None, env="ALPHAVANTAGE_API_KEY")
    NEWSAPI_API_KEY: Optional[str] = Field(None, env="NEWSAPI_API_KEY")
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    CLAUDE_API_KEY: Optional[str] = Field(None, env="CLAUDE_API_KEY")

    # Database
    DATABASE_URL: str = Field("sqlite:///./data/ahos.db", env="DATABASE_URL")

    # Cache
    REDIS_URL: Optional[str] = Field(None, env="REDIS_URL")
    CACHE_TTL: int = Field(3600, env="CACHE_TTL")

    # Rate Limiting
    API_RATE_LIMIT: int = Field(10, env="API_RATE_LIMIT")
    API_MAX_RETRIES: int = Field(3, env="API_MAX_RETRIES")

    # Logging
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field("logs/ahos.log", env="LOG_FILE")

    # AI Agents
    ENABLE_AI_AGENTS: bool = Field(True, env="ENABLE_AI_AGENTS")
    AI_MODEL: str = Field("gpt-3.5-turbo", env="AI_MODEL")
    AI_TEMPERATURE: float = Field(0.7, env="AI_TEMPERATURE")

    # Performance
    MAX_CONCURRENT_REQUESTS: int = Field(10, env="MAX_CONCURRENT_REQUESTS")
    BATCH_SIZE: int = Field(50, env="BATCH_SIZE")

    # Security
    SECRET_KEY: str = Field("change-me-in-production", env="SECRET_KEY")
    ALLOWED_ORIGINS: List[str] = Field(["*"], env="ALLOWED_ORIGINS")

    # Paths
    DATA_DIR: Path = Field(Path("./data"), env="DATA_DIR")
    LOG_DIR: Path = Field(Path("./logs"), env="LOG_DIR")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def allowed_origins_list(self) -> List[str]:
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        return self.ALLOWED_ORIGINS

settings = Settings()
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
