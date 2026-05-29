from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/signalhire"

    # Redis (Upstash free tier or local)
    redis_url: str = "redis://localhost:6379"

    # DeepSeek (primary reasoning LLM)
    deepseek_api_key: str = ""

    # Gemini (LLM parsing/ranking)
    gemini_api_key: str = ""

    # Audit logging
    audit_log_dir: str = "logs"

    # Qdrant (local Docker)
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # Cloudflare R2 (S3-compatible storage)
    r2_access_key: str = ""
    r2_secret_key: str = ""
    r2_account_id: str = ""
    r2_bucket: str = "signalhire"

    # Auth (NextAuth v5 JWT secret)
    auth_secret: str = "change-me-in-production"

    # Ollama (local fallback)
    ollama_base_url: str = "http://localhost:11434/v1"

    class Config:
        env_file = ".env"

settings = Settings()