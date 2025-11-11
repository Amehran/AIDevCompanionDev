"""
Application configuration using Pydantic Settings.

All environment variables and application settings are centralized here.
This follows the 12-factor app methodology for configuration management.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Environment variables can be set in .env file or passed at runtime.
    """
    
    # ===== Application Info =====
    app_name: str = Field(default="AI Dev Companion Backend", description="Application name")
    version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    
    # ===== OpenAI Configuration =====
    # Make optional to avoid crashing app startup when env var is missing.
    # Endpoints that require this key must validate presence at runtime.
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key (optional; required for OpenAI calls)")
    model: str = Field(default="gpt-4o-mini", description="OpenAI model to use")
    model_name: Optional[str] = Field(default=None, description="Alternative model name (legacy)")

    # ===== Optional Third-party APIs (allow presence in .env without failing) =====
    google_api_key: Optional[str] = Field(default=None, description="Google API key (optional)")
    sendgrid_api_key: Optional[str] = Field(default=None, description="SendGrid API key (optional)")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key (optional)")
    crewai_tracing_enabled: Optional[bool] = Field(default=None, description="Enable CrewAI tracing (optional)")
    
    # ===== Server Configuration =====
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # ===== Rate Limiting =====
    rate_limit_per_minute: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Maximum requests per IP per minute"
    )
    max_concurrent_jobs: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum concurrent jobs allowed"
    )
    
    # ===== Logging =====
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)")
    
    # Pydantic v2: model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
        
    @property
    def effective_model(self) -> str:
        """Get the effective model name, preferring model_name over model."""
        return self.model_name or self.model


# Global settings instance
# This will be imported throughout the application
settings = Settings()


def get_settings() -> Settings:
    """
    Dependency function for FastAPI to inject settings.
    
    Usage in FastAPI endpoints:
        @app.get("/")
        def root(config: Settings = Depends(get_settings)):
            return {"app": config.app_name}
    """
    return settings
