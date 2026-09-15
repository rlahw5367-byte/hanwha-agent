from __future__ import annotations

from html import escape

import streamlit as st

from core import api_client, session
from ui.badge import badge_html
from ui.metric import metrics
from ui.table import table

# 부서명과 부서코드를 매핑해놓은 딕셔너리
DEPTS: dict[str, str | None] = {
    "전체": None,
    "인사총무": "HRGA",
    "구매팀": "PU",
    "보안팀": "SE",
    "PMO": "PMO",
}

# 보안 등급
LEVELS = ["전체", "일반", "3급", "대외비"]

# 문서의 상태값
STATUSES = ["전체", "현행", "만료"]

# 문서 목록 표의 제목 (컬럼명)
HEADERS = ["문서 ID", "문서명", "버전", "시행 ~ 만료", "상태", "부서", "등급", "색인"]

# 표 안의 글자 정렬
ALIGNS = ["ag-nowrap", "", "", "ag-nowrap", "", "", "", "ag-nowrap"]

# 화면 상단의 현재 문서 지표 4칸을 그리기
def _metrics_row() -> None:
    try:
        counts = api_client.stats(emp_no=session.emp_no())      # 전체 문서 개수, 현행 상태 문서 개수, 만료상태 문서 개수, 재임베딩 개수
    except api_client.ApiError as exc:
        st.caption(f"지표를 불러오지 못했습니다: {exc}")
        return

    # 지표 4칸 생성
    metrics([
        {"label": "전체", "value": counts["total"], "delta": "문서 버전 기준"},
        {"label": "현행", "value": counts["current"], "delta": "지금 유효한 판",
         "tone": "ok"},
        {"label": "만료", "value": counts["expired"], "delta": "지난 판",
         "tone": "no"},
        {"label": "재임베딩", "value": counts["reindexing"], "delta": "색인을 다시 만드는 중",
         "tone": "wait"},
    ])

# 필터 4개 그리기
def _filter_row() -> dict:
     # 화면 세로로 분할
    left, middle, right, search = st.columns([1, 1, 1, 2])   # 비율 1:1:1:2
    # 각 분할된 화면에 selectbox와 입력란 배치
    with left:
        dept_name = st.selectbox("부서", list(DEPTS), key="f_dept")
    with middle:
        level = st.selectbox("보안등급", LEVELS, key="f_level")
    with right:
        status = st.selectbox("상태", STATUSES, key="f_status")
    with search:
        keyword = st.text_input("검색어", key="f_q", placeholder="문서명 또는 문서 ID")

    # 사용자가 선택한 값을 리턴: 사용자가 선택박스를 전체로 놔두면 None 값으로 리턴
    return {
        "dept_id": DEPTS[dept_name],
        "security_level": None if level == "전체" else level,
        "status": None if status == "전체" else status,
        "q": keyword or None,
    }

# 받아온 문서 목록을 표에 그리기
def _table(documents: list[dict]) -> None:
    rows = []
    for document in documents:
        period = f"{document['effective_from']} ~ {document['expires_at'] or '현행'}"
        index_label = f"{document['index_status']} {document['index_progress']}%"
        # 화면에 그릴 데이터
        rows.append([
            escape(document["doc_id"]),
            escape(document["title"]),
            escape(document["version"]),
            escape(period),
            badge_html(document["status"]),
            escape(document["dept"]),
            escape(document["security_level"]),
            badge_html(index_label),
        ])
    # 테이블에 제목줄과 테이터 줄 추가
    table(HEADERS, rows, align=ALIGNS)

# 화면을 그리기
def render() -> None:
    st.title("문서 관리")
    st.caption("상태 필터가 「전체」라 지난 판까지 함께 보입니다. "
               "「현행」으로 좁히면 현재 유효한 최신본만 남습니다.")

    _metrics_row()   # 지표그리기 호출

    filters = _filter_row()  # 필터 4개 그리기 호출

    if st.button("새 문서 업로드"):  # 문서 업로드 버튼 만들기
        st.info("업로드 화면은 W4 에 만듭니다.")  # 누르면 정보 메세지 출력


    with st.spinner("문서를 불러오는 중입니다..."):
        try:
            #백엔드에 문서 목록 요청
            documents = api_client.list_documents(**filters, limit=100,
                                                  emp_no=session.emp_no())
        except api_client.ApiError as exc:
            st.error(str(exc))
            return

    # 문서가 없다면 아래 정보 메세지 뜸
    if not documents:
        st.info("조건에 맞는 문서가 없습니다. 필터를 바꿔 보세요.")
        return


    st.caption(f"{len(documents)}건")      # 문서 건수 출력
    _table(documents)      # 테이블에 그리기 호출
