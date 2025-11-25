"""Application configuration using Pydantic Settings."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
        # Bedrock Configuration
        bedrock_api_key: Optional[str] = Field(default=None, description="AWS Bedrock API key (required)")
        bedrock_region: Optional[str] = Field(default=None, description="AWS Bedrock region (required)")
        model_id: Optional[str] = Field(default="anthropic.claude-3-sonnet-20240229-v1:0", description="Bedrock model ID")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, description="Rate limit for API requests per minute")
    
    # Job Management
    max_concurrent_jobs: int = Field(default=5, description="Maximum number of concurrent background jobs")
    
    # Pydantic v2: model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars
    )
        
    @property
    def effective_model(self) -> str:
        """Get the effective model name, preferring model_name over model."""
        return self.model_name or self.model


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency function for FastAPI to inject settings."""
    return settings

