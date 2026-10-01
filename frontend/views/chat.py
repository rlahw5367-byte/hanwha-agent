from __future__ import annotations
import streamlit as st
from core import api_client
from ui.card import page_header

def render() -> None:
    page_header('AI 업무 도우미', subtitle="사내 규정을 근거로 답변합니다.")
    if 'chat' not in st.session_state:
        # 채팅 내역 유무 확인 후, 없으면 session에 'chat'이라는 빈 리스트 생성
        st.session_state['chat'] = []
    # 기존 대화내용 화면에 출력
    for message in st.session_state['chat']:
        with st.chat_message(message['role']):
            st.markdown(message['content'])
    # 채팅 입력창 생성
    question = st.chat_input('무엇을 도와드릴까요?')
    if not question:
        return
    # 대화 내역에 질문 추가
    st.session_state['chat'].append({'role': 'user', 'content': question})
    # 질문 화면에 출력
    with st.chat_message('user'):
        st.markdown(question)
    # 답변 화면에 출력
    with st.chat_message('assistant'):
        with st.spinner('사내 규정 찾아보는 중...'):
            try:
                response = api_client.ask(question)
            except api_client.ApiError as e:
                st.error(str(e))
                return
            # 답변 화면에 뿌리기
            answer = response.get('answer', '')
            st.markdown(answer)
        # 대화 내역에 답변 추가
        st.session_state['chat'].append({'role': 'assistant', 'content': answer})
