from pydantic import Field
from pydantic_settings import BaseSettings


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

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = Field("kafka:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    URL_CREATED_TOPIC: str = Field("url_created_events", env="URL_CREATED_TOPIC")

    # Application
    BASE_URL: str = Field("http://localhost:8001", env="BASE_URL")
    DOWNLOAD_TIMEOUT: int = Field(30, env="DOWNLOAD_TIMEOUT")
    METRICS_PORT: int = Field(8000, env="METRICS_PORT")

    BLOOM_EXPECTED_ITEMS: int = Field(10_000_000, env="BLOOM_EXPECTED_ITEMS")
    BLOOM_ERROR_RATE: float = Field(0.0001, env="BLOOM_ERROR_RATE")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
