
from __future__ import annotations
from html import escape
import streamlit as st
from core import api_client, session
from ui.badge import badge_html
from ui.card import page_header, message_block, log_block
from ui.metric import metrics
from ui.table import table, kv_html

HEADERS = ('요청 번호', '내용', '요청자', '실행 유형', '상태', '요청 시각')
ALIGNS = ('ag-nowrap', '', '', '', '', 'ag-nowrap')
TEXT_LIMIT = 40

def _short(text: str) -> str:
    return text if len(text) <= TEXT_LIMIT else text[:TEXT_LIMIT] + '…'

def _metrics_row(summary: dict) -> None:
    avg = summary.get('avg_minutes')
    metrics([{'label': '승인 대기', 'value': summary['waiting'], 'delta': '지금 기다리는 요청', 'tone': 'wait'}, {'label': '오늘 승인', 'value': summary['approved_today'], 'delta': '실행까지 끝난 건', 'tone': 'ok'}, {'label': '오늘 반려', 'value': summary['rejected_today'], 'delta': '사유와 함께 돌려보낸 건', 'tone': 'no'}, {'label': '평균 처리', 'value': '—' if avg is None else f'{avg}분', 'delta': '요청 ~ 결정'}])

def _table(items: list[dict]) -> None:
    rows = [[escape(item['req_id']), escape(_short(item['text'])), escape(item['requester']), escape('Slack 메시지 전송'), badge_html(item['status']), escape(item['requested_at'][:16].replace('T', ' '))] for item in items]
    table(HEADERS, rows, align=ALIGNS)

def render() -> None:
    page_header('승인함', subtitle='외부로 나가는 작업은 승인 후에만 실행됩니다.')
    try:
        with st.spinner('승인 대기 목록을 불러오는 중'):
            data = api_client.list_approvals(session.emp_no())
    except api_client.ApiError as exc:
        st.error(str(exc))
        return
    _metrics_row(data['summary'])
    items = data['items']
    if not items:
        st.info('승인 대기 중인 요청이 없습니다.')
        return
    _table(items)
    
    chosen = _pick(items)
    if chosen:
        _detail(chosen)
        
def _pick(items: list[dict]) -> dict | None:
    if not items:
        return None
    chosen = st.selectbox('상세를 볼 요청', [item['req_id'] for item in items], key='f_req')
    return next((item for item in items if item['req_id'] == chosen), None)

def _detail(item: dict) -> None:
    st.subheader(f"{item['req_id']} · 실행 예정 작업")
    kv_html_text = kv_html([('실행 유형', 'Slack 메시지 전송 ' + badge_html('되돌릴 수 없음', 'no')), ('대상', escape('내 기본 채널(.env 의 SLACK_DEFAULT_CHANNEL)')), ('요청자', escape(item['requester'])), ('근거 문서', '—')])
    st.markdown(kv_html_text, unsafe_allow_html=True)
    st.caption('전송될 메시지')
    message_block(item['text'])
    st.caption("감사 로그")
    log_block(item["events"] or ["기록 없음"])

    _buttons(item)

def _can_decide(user: dict | None) -> bool: 
    return (user or {}).get("role") in ("팀장", "관리자")
    
    
def _buttons(item: dict) -> None:
    can = _can_decide(session.current_user())
    if not can:
        st.caption('승인 권한이 있는 사람만 누를 수 있습니다. (지금 계정: 일반)')
    left, right = st.columns(2)
    with left:
        if st.button('승인 후 실행', key='f_approve', disabled=not can, type='primary'):
            try:
                out = api_client.approve_request(item['req_id'], emp_no=session.emp_no())
            except api_client.ApiError as exc:
                st.error(str(exc))
            else:
                st.success(f"{out['status']} — {out['message']}")
                st.rerun()
    with right:
        note = st.text_input('반려 사유', key='f_note', placeholder='돌려보내는 까닭 한 줄')
        if st.button('반려', key='f_reject', disabled=not can or not note.strip()):
            try:
                out = api_client.reject_request(item['req_id'], note.strip(), emp_no=session.emp_no())
            except api_client.ApiError as exc:
                st.error(str(exc))
            else:
                st.success(f"{out['status']} — {out['message']}")
                st.rerun()