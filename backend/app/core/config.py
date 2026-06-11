from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Enterprise Support Agent API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    secret_key: str = Field(default="replace-with-a-local-dev-secret", alias="SECRET_KEY")
    database_url: str = Field(
        default="mysql+pymysql://root:password@127.0.0.1:3306/enterprise_support_agent?charset=utf8mb4",
        alias="DATABASE_URL",
    )
    access_token_expire_minutes: int = Field(default=60 * 24, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    llm_provider: str = Field(default="mock", alias="LLM_PROVIDER")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        alias="LLM_BASE_URL",
    )
    llm_model: str = Field(default="qwen-plus", alias="LLM_MODEL")
    llm_timeout_seconds: float = Field(default=30.0, alias="LLM_TIMEOUT_SECONDS")
    knowledge_upload_dir: str = Field(
        default="uploads/knowledge",
        alias="KNOWLEDGE_UPLOAD_DIR",
    )
    embedding_provider: str = Field(default="fake", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="fake-embedding-v1", alias="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=64, alias="EMBEDDING_DIMENSION")
    vector_store_path: str = Field(default="data/knowledge_vector_store.json", alias="VECTOR_STORE_PATH")
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
