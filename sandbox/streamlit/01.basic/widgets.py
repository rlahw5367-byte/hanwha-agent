import streamlit as st

st.title("선택과 입력")

st.selectbox("상태", ["python", "fastAPI", "streamlit"], key="f_status")
st.text_input("입력란", key="f_query")
st.checkbox("체크하세요", key="f_check")
st.json({
    "status": st.session_state.f_status,
    "query": st.session_state.f_query,
    "check": st.session_state.f_check
})
