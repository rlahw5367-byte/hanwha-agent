from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.logging import get_logger
from app.models.document import Chunk, DocumentVersion, Document

log = get_logger(__name__)

# 문서 버전의 청크를 모두 재저장하는 함수 (재 임베딩시에도 사용)
def save_chunks(session: Session, version: DocumentVersion, 
                drafts: list, vectors: list[list[float]]) -> int:
    
    # 기존에 저장된 chunks 삭제 
    for old in list(version.chunks):
        session.delete(old)
    session.flush() 

    # 새 청크와 임베딩 벡터 저장 
    for i, (d, vec) in enumerate(zip(drafts, vectors, strict=False)):
        session.add(Chunk(version_id=version.id, ord=i, kind=d.kind,
                          locator=d.locator, text=d.text, embedding=vec))
    version.chunk_count = len(drafts)
    session.flush() 
    log.info("청크 적재 : %s %s - %d청크 - %d벡터", version.doc_id, version.version, len(drafts), len(vectors))
    
    return len(drafts) 


# ----- 검색 ----------------------------------------------
# 검색 결과 한 건을 화면이 그대로 사용할 수 있는 딕셔너리 형태로 변환해주는 함수 
def _row(chunk: Chunk, version: DocumentVersion, doc: Document, score: float) -> dict:
    return {
        "chunk_id": chunk.id,
        "doc_id": doc.id, 
        "title": doc.title, 
        "dept_id": doc.dept_id, 
        "security_level": doc.security_level, 
        "version": version.version, 
        "version_status": version.status, 
        "locator": chunk.locator, 
        "kind": chunk.kind, 
        "text": chunk.text, 
        "score": round(float(score), 4),
    }


# 질문 벡터에 가까운 청크를 가까운 순서대로 리턴해주는 함수 
def vector_search(session: Session, query_vec: list[float], *, limit: int = 12) -> list[dict]:
    if not query_vec:
        return []
    distance = Chunk.embedding.cosine_distance(query_vec).label("distance")
    stmt = (
        select(Chunk, DocumentVersion, Document, distance)
        .join(DocumentVersion, Chunk.version_id == DocumentVersion.id)
        .join(Document, DocumentVersion.doc_id == Document.id)
        .where(Chunk.embedding.is_not(None))
        .order_by("distance")
        .limit(limit)
    )
    return [
        _row(chunk, version, doc, 1.0 - float(dist)) 
        for chunk, version, doc, dist in session.execute(stmt)
    ]
