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
    "법인카드": "카드 결제 사용",
    "재택": "재택근무 원격"
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


# 긴 본문을 화면에 얹을 수 있는 만큼 줄여주는 함수 
def _shorten(text: str, limit:int = 220) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[:limit - 1] + "..."


# 검색 결과 한건을 외부로 내보내는 모양으로 변경 
def source_dict(row: dict) -> dict: 
    return {**row, "score": round(float(row.get("score", 0.0)), 2), 
            "quote": _shorten(row.get("text", ""))}


# 실제 DB를 확인하는 검색기 
class LiveRetriever: 
    name = "live"

    # 질문 하나를 검색 파이프라인에 통과시켜 근거 후보를 리턴해주는 메인 기능 
    def search(self, *, question: str, user: dict, session: Session) -> RetrievalResult:
        settings = get_settings()
        steps: list[dict] = []
        t0 = time.perf_counter()

        #1. 질의 재작성 
        queries = expand_queries(question, settings.multi_query_n)
        steps.append({"name": f"질의 재작성 · Multi-Query {len(queries)}건 생성",
                      "state": "ok", "time": f"{time.perf_counter() - t0:.1f}s"})
        #2. 갈래마다 벡터 검색 -> chunk_id로 중복 제거 
        embedder = get_embedder() 
        seen: dict[int, dict] = {} 
        for one in queries:
            for row in store.vector_search(session, embedder.embed_query(one), limit=settings.retrieval_top_k):
                seen.setdefault(row["chunk_id"], row)
        candidates = sorted(seen.values(), key=lambda r: r["score"], reverse=True)

        # 마무리 : 상위 몇 건만 남기고 최고 점수가 임계값을 넘는지 확인 
        sources = [source_dict(r) for r in candidates[:settings.rerank_top_n]]
        best = max((s["score"] for s in sources), default=0.0)
        return RetrievalResult(sources=sources, steps=steps, best_score=best,
                               passed=best >= settings.retrieval_threshold,
                               threshold=settings.retrieval_threshold)
