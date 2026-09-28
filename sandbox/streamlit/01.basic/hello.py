import streamlit as st

st.set_page_config(page_title="사내 업무 에이전트")

st.title("사내 업무 에이전트")
st.write("화면이 떴다면 성공입니다")   # write는 화면에 텍스트를 출력하는 함수


st.header("헤더")
st.subheader("서브헤더")

st.markdown(
    "- python\n"
    "- fastAPI\n"
    "- streamlit\n"
)

st.divider()

st.caption("출처 - streamlit 공식문서")