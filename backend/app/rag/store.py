from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.document import Chunk, DocumentVersion

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
