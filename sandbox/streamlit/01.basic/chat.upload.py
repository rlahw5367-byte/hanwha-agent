import streamlit as st

st.title("AI 채팅창")

# 채팅 메세지 저장소 없으면 (생성)
if "messages" not in st.session_state:
    st.session_state.messages = []

# 파일 업로드
up = st.file_uploader("문서 올리기", type=["docx", "pdf"])
if up is not None:
    st.SUCCESS(f"받은 파일 - {up.name} ({up.size:,} bytes)")

# 채팅
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["text"])

q = st.chat_input("궁금한 것을 물어보세요")

if q:
    st.session_state.messages.append({"role": "user", "text": q})  # 메세지 저장소에 추가
    with st.chat_message("user"):
        st.write(q)
    with st.chat_message("assistant"):
        st.write("아직 답할 수는 없습니다. 기능 구현은 진도 나가고 가능합니다")


HISTORY = [
    {"role": "user", "text": "출장비 기준이 뭔가요"},
    {"role": "assistant", "text": "DOC-HR-014 제14조입니다"},
    {"role": "user", "text": "광역시는요"},
    {"role": "assistant", "text": "3급 70,000원입니다"},
    {"role": "user", "text": "숙박비 말고 식비는요"},
    {"role": "assistant", "text": "제12조를 보세요"},
]

def trim_history(messages, max_turn=2):
    keep = max_turn *2
    if len(messages) <= keep:
        return messages
    return messages[-keep:]

print(trim_history(HISTORY, max_turn=2)[0]["text"])
