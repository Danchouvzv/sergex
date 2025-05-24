import os
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn


class Settings(BaseSettings):
    """Application settings."""
    
    
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Sergex Air UTM"
    
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/sergexair"
    )
    
    
    MQTT_BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    MQTT_CLIENT_ID: str = os.getenv("MQTT_CLIENT_ID", "sergex_air_backend")
    MQTT_TELEMETRY_TOPIC: str = "drones/+/telemetry"
    
    class Config:
        case_sensitive = True


settings = Settings() 