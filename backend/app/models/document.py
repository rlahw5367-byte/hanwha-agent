from __future__ import annotations

from datetime import date
from sqlalchemy import ForeignKey, String, UniqueConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

# 오류로 인해 임의로 추가함 by. claude _10.07
from pgvector.sqlalchemy import Vector
from app.models.base import EMBED_DIM

# 문서 모델
class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # 자연키
    title: Mapped[str] = mapped_column(String(200))
    dept_id: Mapped[str] = mapped_column(ForeignKey("departments.id"), index=True)
    
    security_level: Mapped[str] = mapped_column(String(10), index=True)  
    
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    dept: Mapped["Department"] = relationship(back_populates="documents")
    owner: Mapped["User | None"] = relationship(back_populates="documents")
    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document",
        order_by="DocumentVersion.version",
    )

    # 현행(시행중인) 버전 리턴
    @property
    def current(self) -> "DocumentVersion | None":
        for v in self.versions:
            if v.status == "현행":
                return v
        return None

# 문서 버전별 저장 모델
class DocumentVersion(Base, TimestampMixin):
    __tablename__ = "document_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    doc_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    version: Mapped[str] = mapped_column(String(10))    
    status: Mapped[str] = mapped_column(String(10))     

    effective_from: Mapped[date]
    expires_at: Mapped[date | None]

    # 파일 자체는 디스크에 두고 DB에는 경로만 저장
    file_path: Mapped[str | None] = mapped_column(String(300))
    file_format: Mapped[str] = mapped_column(String(10))  

    # 색인 관련 (추후 파싱/ 인베딩에 사용될 필드)
    chunk_count: Mapped[int] = mapped_column(default=0)
    embed_model: Mapped[str | None] = mapped_column(String(50))
    index_status: Mapped[str] = mapped_column(String(10), default="대기")  
    index_progress: Mapped[int] = mapped_column(default=0)                
    indexed_at: Mapped[date | None]

    document: Mapped["Document"] = relationship(back_populates="versions")
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="version", cascade="all, delete-orphan")

    
    __table_args__ = (UniqueConstraint("doc_id", "version", name="uq_doc_version"),)

    # 화면에 '시행~만료' 칸에 그대로 들어갈 문자열 리턴
    @property
    def period(self) -> str:
        if self.expires_at is None:
            return f"{self.effective_from} ~"
        return f"{self.effective_from} ~ {self.expires_at}"

    @property
    def is_searchable(self) -> bool:
        return self.status == "현행" and self.index_status == "완료"

# 청크 한 조각 저장할 수 있는 모델
class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("document_versions.id"), index=True)
    ord: Mapped[int] = mapped_column(default=0)    # 문서 안에서의 순서 
    kind: Mapped[str] = mapped_column(String(16))  # "조항" | "표"
    locator: Mapped[str] = mapped_column(String(200)) # "제14조(숙박비) - 별표1" 
    text: Mapped[str] = mapped_column(Text)        # 내용. 표는 마크다운으로 처리   

    version: Mapped["DocumentVersion"] = relationship(back_populates="chunks")
    # 오류로 인해 임의로 추가함 by. claude _10.07
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBED_DIM), nullable=True)

