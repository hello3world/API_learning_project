"""
Application configuration using Pydantic Settings.

This module handles all configuration for the Mining Farm Monitoring API.
Settings are loaded from environment variables and .env file.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        DATABASE_URL: PostgreSQL async connection string.
        SECRET_KEY: Secret key for JWT token signing. MUST be changed in production.
        ALGORITHM: JWT signing algorithm.
        ACCESS_TOKEN_EXPIRE_MINUTES: JWT token expiration time in minutes.
        COOKIE_NAME: Name of the cookie used to store JWT token.
        CORS_ORIGINS: List of allowed CORS origins.
        DEBUG: Enable debug mode (SQLAlchemy echo, etc.).
    """

    # Database
    DATABASE_URL: str = "postgresql+psycopg://mining_user:mining_password@localhost:5433/mining_farm"

    # JWT Configuration
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Cookie Configuration
    COOKIE_NAME: str = "access_token"

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000", "http://localhost:8000"]

    # Application
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra env vars not defined in Settings
    )


# Global settings instance
settings = Settings()
