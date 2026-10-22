import streamlit as st

st.set_page_config(page_title="사내 업무 에이전트")

st.title("사내 업무 에이전트")
st.write("write는 화면에 텍스트를 출력하는 함수입니다.")

st.header("헤더 헤더")
st.subheader("서브 헤더 ")

st.markdown(
    "- python\n"
    "- fastAPI\n"
    "- steamlit\n"
)

st.divider()

st.caption("출처 - streamlit 공식 문서")
