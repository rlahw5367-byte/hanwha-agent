import pathlib
import sys

# 프로젝트 실행을 root에서 하기 때문에 frontend 경로 등록해주기 
sys.path.insert(0, str(pathlib.Path(__file__).parent)) # frontend/를 모듈 검색 경로에 넣는다. 

import streamlit as st 

from ui.theme import inject_css

# 가장 먼저 부르는 st 함수여야 한다. 최상위에 배치
st.set_page_config(
    page_title = "사내업무 에이전트",
    layout = "wide",
    initial_sidebar_state = "expanded",
)

inject_css()  # css 적용

# 사이드바 내비 항목
NAV: list[tuple[str, str | None]] = [
    ("AI 업무 도우미", None),
    ("문서 관리", "documents"),
    ("승인함", None),
    ("운영 대시보드", None)
]

# 사이드바 그리는 함수 
def render_sidebar() -> None:
    st.sidebar.markdown(
        '<div class="ag-brand"><div class="ag-brand-name">사내 업무 에이전트</div></div>',
        unsafe_allow_html=True,
    )

    for label, page_key in NAV:
        if st.sidebar.button(label, key=f"nav_{label}"):
            if page_key is None:
                st.sidebar.info("아직 만들지 않은 화면")
            else:
                st.session_state["page"] = page_key


# 메인
def main() -> None:
    st.session_state.setdefault("page", "document")

    render_sidebar()

    page = st.session_state["page"]
    if page == "documents":
        st.info("문서 목록 화면은 다음 시간에 만들겠습니다.")
    else:
        st.info("아직 만들지 않은 페이지와 서버입니다.")

main()

