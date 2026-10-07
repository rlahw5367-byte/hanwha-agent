from __future__ import annotations

import time

from sqlalchemy import text

REPEAT = 10
TOP_K = 5    
WIDTH = 88

PICK = text("SELECT embedding::text FROM chunks "
            "WHERE embedding IS NOT NULL ORDER BY id LIMIT 1")
SEARCH = ("SELECT id FROM chunks WHERE embedding IS NOT NULL "
          "ORDER BY embedding <=> CAST(:q AS vector) LIMIT :k")
NOISE = ("Sort Key", "Sort Method", "Buffers", "Planning", "Execution")

def average_ms(session, qvec: str) -> float:
    started = time.perf_counter()       
    for _ in range(REPEAT):
        session.execute(text(SEARCH), {"q": qvec, "k": TOP_K}).all()
    return (time.perf_counter() - started) / REPEAT * 1000


def show_plan(session, qvec: str, *, seqscan: str) -> None:
    print(f"\n[ enable_seqscan = {seqscan} ]")
    session.execute(text(f"SET enable_seqscan = {seqscan}"))
    rows = session.execute(text("EXPLAIN ANALYZE " + SEARCH),
                           {"q": qvec, "k": TOP_K}).all()
    for (line,) in rows:
        if line.strip().startswith(NOISE):  
            continue
        print(line[:WIDTH] + (" ..." if len(line) > WIDTH else ""))


def main() -> None:
    try:
        from app.db.session import session_scope
        with session_scope() as s:
            qvec = s.execute(PICK).scalar()
            if qvec is None:
                print("벡터가 든 청크가 한 줄도 없습니다. 문서 한 건 올린 뒤 다시 돌리세요.")
                return
            print(f"같은 질의 {REPEAT}회 평균 : {average_ms(s, qvec):.1f} ms")
            show_plan(s, qvec, seqscan="off")  
            show_plan(s, qvec, seqscan="on")   
            print("\n계획은 바뀌었다. 시간은 이 규모에서 바뀌지 않는다.")
    except Exception as exc:                   
        print(f"DB 에 붙지 못했습니다: {type(exc).__name__} — docker compose up -d 로 "
              "postgres 를 먼저 띄운 뒤 다시 돌리세요.")


if __name__ == "__main__":
    main()