from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse 
# from app.api.v1.documents import router as documents_router  # 지우기 
# from app.api.v1.auth import router as auth_router  # 지우기 
from app.api.v1 import auth, documents # 하나로 통합 
from app.core.exceptions import AgentError
from contextlib import asynccontextmanager
from app.core.logging import setup_logging
from fastapi.exceptions import RequestValidationError


# lifespan 함수 정의 
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging() 
    yield

# FastAPI 앱 생성 
app = FastAPI(
    title="사내 AI 에이전트", 
    version="0.1.0", 
    lifespan=lifespan
)

# 서버 상태 확인용 API
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

# 라우터 연결 
app.include_router(
    documents.router, 
    prefix="/api/v1"
)

app.include_router(
    auth.router,
    prefix="/api/v1"
)

@app.exception_handler(AgentError)
async def handle_agent_error(
    request: Request, 
    exc: AgentError
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code, 
        content={
            "code": exc.code, 
            "message": str(exc), 
            "detail": None
        }
    )

# 사번 입력 안하고 로그인시 비번 로그에 노출 -> 예외로 잡기 
@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    # exc.errors() 에는 사용자가 보낸 값이 통째로 들어 있다. 필드 이름만 돌려주고 값은 감춘다.
    fields = ", ".join(
        ".".join(str(p) for p in e["loc"][1:]) or "요청 본문" for e in exc.errors()
    )
    return JSONResponse(
        status_code=422,
        content={"code": "validation_failed", "message": f"입력값을 확인하세요 — {fields}", "detail": None},
    )