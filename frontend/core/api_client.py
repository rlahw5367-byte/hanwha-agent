from __future__ import annotations

import os
from typing import Any
import httpx2

BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")

TIMEOUT = 10.0

# 백엔드 호출 실패시 예외 클래스 
class ApiError(RuntimeError):
    pass

# 모든 호출이 지나가는 내부 공용 함수
def _request(
    method: str,  # GET,POST 전송방식 
    path: str,    # BASE_URL 뒤에 붙는 경로 ex. /api/v1/documents
    *,
    params: dict | None = None,  # 쿼리스트링 ?aaa=10
    json: dict | None = None,    # 요청 본문으로 보낼 dict 타입 데이터 
    emp_no: str | None = None,   # 사원번호. X-Emp-No 헤더값 
) -> Any:

    clean_params = None
    if params is not None: # 파라미터가 있다면 
        # None,빈문자열,전체라는 값이 아닌 파라미터값들만 파라미터로 취합 
        clean_params = {k: v for k, v in params.items() if v not in (None, "", "전체")}

    # emp_no가 넘어오면 헤더 정보로 추가 
    headers = {"X-Emp-No": emp_no} if emp_no else None
    # 요청할 URL 완성 
    url = f"{BASE_URL}{path}"

    try:
        # 백엔드에 요청 
        response = httpx2.request(
            method, url, params=clean_params, json=json, headers=headers, timeout=TIMEOUT
        )
    except httpx2.ConnectError as exc:
        raise ApiError(
            f"백엔드에 연결하지 못했습니다. 터미널에서 서버가 떠 있는지 확인하세요 ({BASE_URL})."
        ) from exc
    except httpx2.TimeoutException as exc:
        raise ApiError("응답이 너무 늦습니다. 서버가 멎었는지 확인하세요.") from exc

    # 요청 4xx, 5xx 발생시 
    if response.status_code >= 400:
        try:
            message = response.json().get("message") or response.text
        except ValueError:
            message = response.text
        raise ApiError(message)

    # 응답 데이터 리턴 
    return response.json()

# 로그인 요청 
def login(emp_no: str, password: str) -> dict:
    return _request("POST", "/api/v1/auth/login", json={"emp_no": emp_no, "password": password})

# 현재 사용자를 백엔드에 다시 물어보기 
def me(emp_no: str) -> dict:
    return _request("GET", "/api/v1/auth/me", emp_no=emp_no) # 백엔드에 요청 

# 문서 데이터 목록 요청 
def list_documents(
    *,
    dept_id: str | None = None,
    security_level: str | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = 20,
    emp_no: str | None = None, # 신원 함께 보내기 
) -> list[dict]:
    params = {
        "dept_id": dept_id,
        "security_level": security_level,
        "status": status,
        "q" : q,
        "limit": limit
    }
    return _request("GET", "/api/v1/documents", params=params, emp_no=emp_no) # 백엔드에 요청 

# 문서 한건 요청 
def get_document(doc_id: str, *, emp_no: str | None = None) -> dict:
    return _request("GET", f"/api/v1/documents/{doc_id}", emp_no=emp_no)

# 나중에 문서상태 화면에 뿌려줄 데이터 요청 
def stats(*, emp_no: str | None = None) -> dict:
    rows = list_documents(limit=100, emp_no=emp_no)
    return {
        "total": len(rows), 
        "current": sum(1 for row in rows if row["status"] == "현행"), 
        "expired": sum(1 for row in rows if row["status"] == "만료"),
        "reindexing" : sum(1 for row in rows if row["index_status"] == "재임베딩 ")
    }