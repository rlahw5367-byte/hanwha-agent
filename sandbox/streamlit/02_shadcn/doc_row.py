import streamlit as st
import streamlit_shadcn_ui as ui

st.title("화면 04 한 줄을 shadcn 으로 만들어 본다")

rows = [
    {"문서ID": "DOC-HR-014", "문서명": "국내출장 여비 규정", "상태": "현행", "청크": 70},
    {"문서ID": "DOC-SE-011", "문서명": "장비 반출입 절차", "상태": "만료", "청크": 24},
]
cols = [
    {"key": "문서ID", "label": "문서 ID"},
    {"key": "문서명", "label": "문서명"},
    {"key": "상태", "label": "상태"},
    {"key": "청크", "label": "청크", "align": "right"},   # 우측 정렬은 된다
]
ui.table(data=rows, columns=cols, key="doc_table")


st.divider()
st.subheader("여기서 막힌다")
st.write("상태 칸에 **배지**를 넣고 싶다. 그런데 표의 칸은 글자만 받는다.")