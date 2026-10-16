# 리랭킹 -  찾아온 후보의 순위를 다시 매기는 기능 

from __future__ import annotations

import re 

_TOKEN = re.compile(r"[가-힣A-Za-z0-9]")

# 글을 두 글자 이상인 낱말의 집합(중복제거)으로 변경 해주는 함수 
def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN.findall(text or "") if len(t) > 1}


# 질의의 낱말 중 몇 퍼센트이 본문에 있는지 검증하는 함수 
def score(query: str, text: str) -> float:
    q, d = _tokens(query), _tokens(text)
    if not q or not d:
        return 0.0
    return len(q & d) / len(q)

# 간이 리랭커 : 벡터 점수와 어휘 중복률을 섞은 값을 rerank_score에 작성 
def _simple(query: str, pool: list[dict], vector_weight: float) -> None:
    for c in pool:
        lexical = score(query, c.get("text", ""))
        bonus = 0.03 if c.get("kind") == "표" else 0.0 
        c["rerank_score"] = round(
            vector_weight * c.get("score", 0.0) + (1 - vector_weight) * lexical + bonus, 4
        )
        c["rerank_by"] = "simple"


# 후보의 순위를 다시 매기고, 상위 몇 건만 남겨서 리턴 
def rerank(query: str, candidates: list[dict], top_n: int = 3, 
           *, vector_weight: float = 0.7) -> list[dict]:
    _simple(query, candidates, vector_weight)
    ranked = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)
    return ranked[:top_n]
