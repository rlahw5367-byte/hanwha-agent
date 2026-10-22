import streamlit as st

def page_chat():
    st.title("AI 업무 도우미 채팅창")
    st.write("여기에 채팅 화면이 들어갑니다...")

def page_doc():
    st.title("문서 관리 페이지")
    st.write("문서 목록들이 들어갑니다...")

# 함수 하나가 페이지 하나 
pages = [
    st.Page(page_chat, title="AI Chat"),
    st.Page(page_doc, title="문서 관리")
]

st.navigation(pages).run()