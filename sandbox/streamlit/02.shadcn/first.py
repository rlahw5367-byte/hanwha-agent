import streamlit as st
import streamlit_shadcn_ui as ui

st.title("shadcn 사용해보기")

ui.card(
    title="나의 첫 카드",
    description= "내용 설명글",
    content = "실제 내용 내용",
    key="my_card",
)

ui.badge("뱃지1", key="b_now")
ui.badge("뱃지2", key="b_sec", variant="secondary")

ui.metric_card("전체 문서", "42", description="지난주 대비 +3", key="m1")

if ui.button("문서 열기", key="open_btn"):
    st.write("눌렀습니다")