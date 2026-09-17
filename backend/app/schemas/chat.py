# 채팅 요청과 응답 스키마 
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

DOC_IDS = Literal["DOC-HR-014", "DOC-PU-007", "DOC-SE-003"] # 임시 

# 사용자가 보내오는 질문 하나 담아주는 객체(모델)
class ChatRequest(BaseModel):
    question: str = Field(
        min_length=2,
        max_length=2000, 
        description="사용자 질문. 두 글자 이상 2000자 이하"
    )

# 답변이 인용한 근거 한개 담아줄 객체(모델)
class AnswerSource(BaseModel):
    doc_id: DOC_IDS = Field(description="인용한 문서 번호. 등록된 세 건 중 하나") # 임시 
    title: str = Field(description="문서 제목")
    version: str = Field(description="문서 버전. 예: v2.0")
    locator: str = Field(description="문서 안 위치. 예: 제12조 - p.6")

# 모델이 돌려줘야하는 답변의 모양 
class AnswerOut(BaseModel):
    answer: str = Field(description="한국어 답변 본문")
    sources: list[AnswerSource] = Field(description="답변이 인용한 근거 목록")
    enough_evidence: bool = Field(description="근거가 충분했는가. 부족하면 False")

