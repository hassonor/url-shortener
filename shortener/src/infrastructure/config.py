"""
config.py

Provides configuration settings for the URL shortener service using pydantic's BaseSettings.
Loads values from environment variables.
"""

from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # Logging
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field("%(asctime)s [%(levelname)s] %(name)s: %(message)s", env="LOG_FORMAT")

    # PostgreSQL
    PG_HOST: str = Field("postgres", env="PG_HOST")
    PG_PORT: int = Field(5432, env="PG_PORT")
    PG_USER: str = Field("postgres", env="PG_USER")
    PG_PASSWORD: str = Field("password", env="PG_PASSWORD")
    PG_DATABASE: str = Field("shortener", env="PG_DATABASE")

    # Redis
    REDIS_HOST: str = Field("redis", env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")
    REDIS_DB: int = Field(0, env="REDIS_DB")

    # Application
    BASE_URL: str = Field("http://localhost:8080", env="BASE_URL")

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
