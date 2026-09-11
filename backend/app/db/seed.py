
"""
시드를 적재한다. 몇 번을 돌려도 결과가 같아야 한다(멱등).
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.seed_data import DEPARTMENTS, DOCUMENTS, USERS
from app.db.session import session_scope
from app.models import Department, Document, DocumentVersion, User

# 4개의 행의 수를 돌려주는 함수
def count_rows(session: Session) -> dict[str, int]:

    return {
        "departments": session.scalar(select(func.count()).select_from(Department)) or 0,
        "users": session.scalar(select(func.count()).select_from(User)) or 0,
        "documents": session.scalar(select(func.count()).select_from(Document)) or 0,
        "versions": session.scalar(select(func.count()).select_from(DocumentVersion)) or 0,
    }

# 비어있을 때만 적재하는 함수
def seed_all(session: Session | None = None) -> dict[str, int]:

    if session is not None:
        return _seed(session)
    with session_scope() as s:
        return _seed(s)

# 실제로 적재 처리하는 함수 (별도로 분리)
def _seed(session: Session) -> dict[str, int]:
    # 적재된게 있는지 체크 : 있으면 개수만 세어 리턴
    if session.scalar(select(func.count()).select_from(Document)):
        return count_rows(session)
    
    # 적재된게 없다
    session.add_all(Department(**row) for row in DEPARTMENTS) # 부서
    session.add_all(User(**row) for row in USERS) # 사용자
    session.flush()   

    # 문서 적재
    for doc in DOCUMENTS:
        # dict에서 version만 빼낸다
        fields = {k: v for k, v in doc.items() if k != "versions"}
        # 문서 저장
        session.add(Document(**fields))
        session.flush()
        # 문서 버전들 저장
        session.add_all(
            DocumentVersion(doc_id=doc["id"], **ver) for ver in doc["versions"]
        )
    session.flush()

    # 적재된 카운트 리턴
    return count_rows(session)
