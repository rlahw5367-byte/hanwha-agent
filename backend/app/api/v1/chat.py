from __future__ import annotations

# 채팅 라우터 
from fastapi import APIRouter
from app.schemas.chat import AskOut, ChatRequest
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])

# 채팅 질문 요청 -> 답변 돌려주기 
@router.post("/messages", response_model=AskOut)
def create_message(payload: ChatRequest) -> AskOut:
    # 서비스에게 사용자 질문 주고 로직처리 시키기 
    return chat_service.ask(question=payload.question) 

# * 추가 *
# 실행 기록 한건 조회 
@router.get("/runs/{run_id}")
def read_run(run_id: str) -> dict:
    # 서비스에게 run_id주고 DB에서 실행 기록 한개 조회해오도록 시키기 
    return chat_service.get_run(run_id=run_id)