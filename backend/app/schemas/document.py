# 문서 정보 응답해줄때 사용할 스키마 
from pydantic import BaseModel, Field
from typing import Literal
from datetime import date

# 사용자/화면에 전달해도 되는 정보들만 모아서 클래스로 구성 
class DocumentOut(BaseModel):
    doc_id: str
    title: str
    dept: str
    version: str
    security_level: Literal["일반", "3급", "대외비"]
    file_format: Literal["docx", "pdf"]
    status: Literal["현행", "만료"]

		# 추가 
    effective_from: date
    expires_at: date | None = None
    index_status: Literal["대기", "재임베딩", "완료", "보관"] = "대기"
    index_progress: int = Field(default=0, ge=0, le=100)

# 업로드 응답: 무엇이 어디에 저장됐는지만 알려주는 객체
class DocumentCreateOut(BaseModel):
    doc_id: str = Field(examples=["DOC-HR-014"])
    title: str
    version: str = Field(examples=["v2.0"])
    file_format: Literal["docx", "pdf"]
    file_path: str = Field(examples=["uploads/DOC-HR-014_v2.0.docx"])
    created: bool = Field(
        description="문서 자체가 이번에 새로 생겼으면 True, 버전만 더했으면 False"
    )
