from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://knowledge_user:knowledge_password@localhost:5432/knowledge_assistant"

    llm_provider: str = "gemini"
    llm_model: str = "gemini-flash-lite-latest"
    gemini_api_key: str = ""

    embedding_provider: str = "local"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimensions: int = 384
    retrieval_min_similarity_score: float = 0.05
    upload_dir: str = "uploads"
    max_upload_bytes: int = 26_214_400
    max_docx_uncompressed_bytes: int = 104_857_600

    cors_origins: str = "http://localhost:3000"
    session_cookie_name: str = "knowledge_assistant_session"
    session_lifetime_days: int = 7
    session_cookie_secure: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
