from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from functools import lru_cache
from app.models.base import EMBED_DIM


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False  # APP_MODE 든 app_mode든 같은것으로 보게 설정 
    )

    app_mode: str = Field(default="mock", pattern=r"^(mock|live)$")
    # --- LLM ----------------------------------------------------------
    anthropic_api_key: SecretStr | None = None 
    llm_model: str = "claude-haiku-4-5"
    max_tokens: int = Field(default=400, ge=1, le=8192)
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    # --- 안전장치 -----------------------------------------------------
    daily_call_limit: int = Field(default=200, ge=1)
    max_input_chars: int = Field(default=200, ge=1)
    # --- DB -----------------------------------------------------------
    database_url: str = "sqlite:///./app.db"
    # --- 기본 설정 ----------------------------------------------------
    debug: bool = False
    allow_external_send: bool = False
    # --- 관측 langfuse -------------------------------------------------
    langfuse_enabled: bool = False 
    langfuse_host: str = "http://localhost:3000"
    langfuse_public_key: str | None = None
    langfuse_secret_key: SecretStr | None = None
    # --- Upstage 추가 ------------------------------------------------------
    upstage_api_key: SecretStr | None = None
    upstage_base_url: str = "https://api.upstage.ai/v1"
    upstage_parse_model: str = "document-parse"
    upstage_parse_ocr: str = "auto"  

    # --- Embedding ------------------------------------------------------
    embed_provider: str = Field(
        default="local",
        pattern=r"^(local|upstage)"
    )
    embed_model_dir: str = "../models/bge-m3"
    embed_dim: int = EMBED_DIM
    upstage_embed_model: str | None = None

# 추가 
    # --- 검색 -----------------------------------------------------------
    retrieval_threshold: float = Field(default=0.55, ge=0.0, le=1.0) # 임계값. 점수를 넘지 못하면 근거 부족 
    retrieval_top_k: int = Field(default=12, ge=1, le=100)  # 벡터 검색이 받아올 후보 갯수 
    # 아래 두 줄 추가 
    multi_query_n: int = Field(default=3, ge=1, le=10) # 질문을 몇 갈래까지 늘리는가   
    rerank_top_n: int = Field(default=3, ge=1, le=20) # 다시 줄 세운 뒤 몇 건을 남길 것인가


    # live 모드인지 확인 -> settings.is_live => True/Fase 
    @property
    def is_live(self) -> bool:
        return self.app_mode == "live"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def mask(secret: str | None, keep: int = 8) -> str:
    if not secret:
        return "(없음)"
    return f"{secret[:keep]}...({len(secret)}자)"

