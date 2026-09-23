from __future__ import annotations
import time 
import app.integrations.factory as factory 
from pydantic import ValidationError
from app.core.guards import check_question
from app.core.logging import get_logger
from app.core.config import get_settings
from app.core.exceptions import NotFound
from app.db.session import session_scope
from app.models import Run, UsageLog
from app.services.ids import next_run_id
from app.schemas.chat import AnswerOut, AskOut
from app.agent.chain import build_result_chain


log = get_logger(__name__)

# 첫 호출 1회 + 재시도 2회 = 3회 
MAX_ATTEMPTS = 3

# 폴백 답변 본문
FALLBACK_ANSWER = "요청을 처리했지만 근거를 확인하지 못했습니다. 담당 부서에 문의해 주세요."

# 질문자 (임시)
DEFAULT_USER = {"name": "김민준", "dept": "인프라사업부 2팀"}

# 근거 문서 목록. 
NO_CONTEXTS: list[dict] = []

# pydantic 의 오류 목록을 모델에게 다시 보낼 한 줄의 문장으로 변경해서 리턴 : 재시도 힌트 
def _hint_from(errors: list[dict]) -> str:
    # errors : ValidationError 가 돌려주는 목록 
    parts = []
    for err in errors:
        where = ".".join(str(x) for x in err.get("loc", ())) or "(최상위)"
        parts.append(f"{where}: {err.get('msg', '')}")
    return "/".join(parts)

# fallback : 재시도 다 사용뒤 사용자에게 보낼 답 리턴해주는 함수 
def _fallback(run_id: str, attemps: int) -> AskOut:
    # 사용자에게 응답해줄 최종 응답 결과 
    return AskOut(
        answer=FALLBACK_ANSWER, 
        sources=[], 
        enough_evidence=False, 
        run_id=run_id,
        attempts=attemps, 
        fallback_used=True
    )

# 호출 한번의 사용량과 원가를 usage_logs에 남기는 함수 
def _record_usage(run_id: str, result) -> None:
    # run_id : 실행 고유번호 
    # result : 어댑터가 돌려준 LLMResult 타입 응답데이터 
    try:
        with session_scope() as session:
            session.add(
                UsageLog(
                    run_id=run_id, 
                    model=result.model, 
                    input_tok=result.input_tok, 
                    cache_tok=result.cache_tok, 
                    output_tok=result.output_tok, 
                    cost_krw=result.cost_krw
                )
            )
    except Exception as e:
        log.warning("사용 기록 실패(무시하고 계속): %s", e)


# 본체 : 질문 하나에 대답하기 
def ask(*, question: str, run_id: str | None = None, user_id: int = 1) -> AskOut:
    #1. 가드 호출 -> 여기서 던져진 예외는 이 함수를 통과해 전역 핸들러까지 올라간다. 
    q = check_question(question) 

    # 2. 어댑터 한 개. 
    llm = factory.get_llm() 

    # 체인 생성
    chain = build_result_chain(llm, contexts=NO_CONTEXTS, user=DEFAULT_USER).with_retry(
        stop_after_attempt=2
    )

    # day15 추가 
    from app.integrations.langfuse_client import score, trace
    from app.integrations.llm_claude import _extract_json 

    started = time.perf_counter() # 시작시간 

    # 질문 정보 DB Run에 저장 
    with session_scope() as session:
        if run_id is None:
            run_id = next_run_id(session) # run_id 없으면 생성 
        session.add(
            Run(
                id=run_id, 
                user_id=user_id, 
                question=q, 
                status="진행중",
                mode=get_settings().app_mode
            )
        )

    # langfuse 감싸서 llm 요청 
    with trace(
        "ask", 
        run_id=run_id,
        user_id=str(user_id),
        metadata={"question_len" : len(q)},
    ):
        out = None
        hint = ""
        for attempt in range(1, MAX_ATTEMPTS + 1):
            # 3. llm 호출 
            #   프롬프트 준비 
            prompt = q if not hint else f"{q}\n\n[직전 응답의 문제] {hint}\n출력 형식을 지켜 다시 답해 주세요."
            #   llm에 질문 던지기 
            result = chain.invoke({"question": prompt})

            # 검증 전에 usage_log 기록 하기 
            _record_usage(run_id, result)

            try:
                data = _extract_json(result.text)
                AnswerOut.model_validate(data)   # 규격에 맞는지 검사하는 부분 
            except ValidationError as e:
                hint = _hint_from(e.errors(include_url=False))
                # log.warning(f"스키마 위반 {attempt}/{MAX_ATTEMPTS}회 : {hint}")
                log.warning("스키마 위반 %d/%d회 : %s", attempt, MAX_ATTEMPTS, hint)
                continue 

            # 통과 시 out 변수에 담기 
            out = AskOut(**data, run_id=run_id, attempts=attempt, fallback_used=False)
            break 
        # end of for 

        if out is None:
            # 3번 다 시도했다. 로그 남기고, 폴백 실행 
            log.warning("스키마 검증에 %d회 모두 실패하여 폴백으로 응답합니다.(run_id=%s)", MAX_ATTEMPTS, run_id)
            out = _fallback(run_id, MAX_ATTEMPTS)
            score(run_id, "schema_ok", 0.0)

        with session_scope() as session:
            run = session.get(Run, run_id)  # run_id에 해당하는 레코드 한개 조회 
            run.answer = out.answer
            run.status = "완료"
            run.latency_ms = int((time.perf_counter() - started) * 1000)
            run.sources = [s.model_dump() for s in out.sources]

        return out 


# 실행 기록 한 건 조회 
def get_run(*, run_id: str) -> dict:
    with session_scope() as session:
        run = session.get(Run, run_id) # PK로 레코드 한건 조회 
        if run is None:
            raise NotFound(f"실행 기록을 찾을 수 없습니다: {run_id}")
        return {
            "run_id": run_id, 
            "user_id": run.user_id, 
            "question": run.question,
            "answer": run.answer, 
            "status": run.status,
            "latency_ms":  run.latency_ms, 
            "mode": run.mode,
            "sources": run.sources or [], 
            "created_at": run.created_at.isoformat(),
        }






