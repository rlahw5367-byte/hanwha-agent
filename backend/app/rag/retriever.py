# 검색 파이프라인 - 질문 하나를 근거가 될 만한 조각으로 변경하는 파일 

from __future__ import annotations

import time 

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.integrations.factory import get_embedder
from app.integrations.ports import RetrievalResult
from app.rag import store

log = get_logger(__name__)

# 사람이 사용하는 낱말 -> 규정이 사용하는 낱말 
SYNONYMS = {
    "출장비": "여비 일비 숙박비 식비", 
    "여비": "출장비 일비 숙박비",
    "숙박": "숙박비 호텔 1박", 
    "교통": "교통비 KTX 항공",
    "기준": "규정 상한 지급 기준표",
    "신청서": "신청 양식 서식",
}

# 질문을 여러 각도로 고쳐 작성 -> 목록으로 리턴 
def expand_queries(question: str, n: int = 3) -> list[str]:
    q = (question or "").strip()  
    out = [q]   # 1. 원문 (오리지널 사용자 질문)
    extra = " ".join(v for k, v in SYNONYMS.items() if k in q)
    if extra:
        out.append(f"{q} {extra}")  # 2. 가상 사전에 걸리는 낱말이 있으면 동의어를 뒤에 덧붙인 질문 추가 

    # 3. 한 글자짜리 조사,군더더기 문자를 걷어내고, 남은 핵심어만으로 된 질문 
    core = " ".join(t for t in q.split() if len(t) > 1)[:120]
    if core and core != q:
        out.append(core)

    return out[:n]