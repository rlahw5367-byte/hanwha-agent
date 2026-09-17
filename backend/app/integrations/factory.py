# mock / live 분기의 유일한 지점
from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.core.exceptions import ModeNotAvailable
from app.integrations.ports import LLMPort

# Claude 어댑터를 하나 만들어두고, 재사용하기
@lru_cache
def _live_llm() -> LLMPort:
    from app.integrations.llm_claude import ClaudeLLM
    return ClaudeLLM()

# 지금 설정에 맞는 LLM 어댑터를 돌려주는 함수
def get_llm() -> LLMPort:
    settings = get_settings()  # 환경 설정 정보 가져오기
    if not settings.is_live  # live 가 아니다
    raise ModeNotAvailable(
        "테스트용 mock 어댑터는 만들지 않았습니다."
        ".env의 APP_MODE 를 live로 두고 터미널에서 부르세요."
    )
    return _live_llm()


