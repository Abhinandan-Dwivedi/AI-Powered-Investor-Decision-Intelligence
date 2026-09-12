"""
Centralized application configuration.

Every setting the app needs lives here, sourced from environment
variables (.env locally, real env vars in production). No other
module should call os.getenv directly — import `settings` instead.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    app_name: str = "AI-Powered Investor Intelligence Platform"
    environment: str = "development"  # development | production

    # --- Postgres ---
    # Local dev: docker-compose Postgres. Production: Supabase connection string.
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "investor_intel"
    postgres_sslmode: str = "disable"  # "require" in production (Supabase)

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            f"?sslmode={self.postgres_sslmode}"
        )

    # --- Qdrant ---
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None  # required for Qdrant Cloud in production
    qdrant_collection: str = "financial_documents"

    # --- LLM provider ---
    # We use direct provider APIs, not cloud wrappers (Azure, etc.)
    llm_provider: str = "gemini"  # "openai" | "anthropic" | "gemini"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None

    chat_model: str = "gemini-flash-latest"
    extraction_model: str = "gemini-flash-latest"
    embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 1536  # Gemini supports scaling down from 3072 via MRL

    # --- Retrieval ---
    retrieval_top_k: int = 20
    rerank_top_k: int = 6

    # --- Ingestion ---
    max_upload_size_mb: int = 25
    raw_pdf_dir: str = "data/raw_pdfs"
    markdown_dir: str = "data/markdown"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — import this everywhere via `settings`."""
    return Settings()


settings = get_settings()
