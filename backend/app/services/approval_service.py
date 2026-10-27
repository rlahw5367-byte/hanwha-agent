# 승인 서비스 
from __future__ import annotations

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.exceptions import ExternalServiceError, ModeNotAvailable, NotFound, PermissionDenied
from app.db.session import session_scope
from app.models import ApprovalRequest, AuditLog, User
from app.tools import registry

# 상태값 세트
WAITING, APPROVED, DONE, REJECTED = ('대기중', '승인', '승인·실행', '반려됨')
# 첫 요청 번호
REQ_START = 148

def _next_req_id(session: Session) -> str:
    numbers = [REQ_START - 1]
    for req_id in session.scalars(select(ApprovalRequest.id)).all():
        tail = req_id.removeprefix('REQ-')
        if tail.isdigit():
            numbers.append(int(tail))
    return f'REQ-{max(numbers) + 1:04d}'

def _draft(state: dict) -> dict:
    return {'text': state['text']}

def _send(state: dict) -> dict:
    registry.load_all()
    try:
        return {'result': registry.get('send_slack').fn(text=state['text'])}
    except ModeNotAvailable:
        return {'result': {'ok': False, 'error': '전송 꺼짐'}}
    except ExternalServiceError as e:
        return {'result': {'ok': False, 'error': e.message}}

def build_graph(checkpointer):
    from app.agent.graph import build_approval_graph
    return build_approval_graph(_draft, _send, checkpointer=checkpointer)

def _resume(checkpointer, thread_id: str, decision: dict) -> dict:
    from langgraph.types import Command
    return build_graph(checkpointer).invoke(Command(resume=decision), {'configurable': {'thread_id': thread_id}})

def open_request(*, thread_id: str, requester_id: int, text: str, run_id: str | None=None) -> str:
    with session_scope() as s:
        requester = s.get(User, requester_id)
        if requester is None:
            raise NotFound(f'없는 사용자: {requester_id}')
        req_id = _next_req_id(s)
        s.add(ApprovalRequest(id=req_id, thread_id=thread_id, run_id=run_id, requester_id=requester_id, action_type='slack', payload={'text': text}, status=WAITING))
        s.add(AuditLog(approval_id=req_id, run_id=run_id, actor=requester.name, event='Slack 전송 요청 → 승인 대기', detail=text))
    return req_id

def events(req_id: str) -> list[str]:
    with session_scope() as s:
        return list(s.scalars(select(AuditLog.event).where(AuditLog.approval_id == req_id).order_by(AuditLog.id)))

def _close(req_id: str, status: str, event: str, text: str | None=None) -> None:
    with session_scope() as s:
        row = s.get(ApprovalRequest, req_id)
        row.status = status[:24]
        if text is not None:
            row.payload = {'text': text}
        s.add(AuditLog(approval_id=req_id, run_id=row.run_id, actor='시스템', event=event[:64]))


def _decide(req_id: str, approver_id: int, status: str, event: str, note: str='') -> ApprovalRequest:
    with session_scope() as s:
        row, user = (s.get(ApprovalRequest, req_id), s.get(User, approver_id))
        if row is None:
            raise NotFound(f'없는 승인 요청: {req_id}')
        if row.status != WAITING:
            raise PermissionDenied(f'이미 처리된 요청: {row.status}')
        if user is None or not user.can_approve:
            raise PermissionDenied('승인 권한이 없습니다')
        row.status, row.approver_id, row.decided_at = (status, approver_id, datetime.now())
        s.add(AuditLog(approval_id=req_id, run_id=row.run_id, actor=user.name, event=event, detail=note))
    return row

def approve(*, req_id: str, approver_id: int, checkpointer) -> dict:
    row = _decide(req_id, approver_id, APPROVED, '승인')
    try:
        out = _resume(checkpointer, row.thread_id, {'approved': True, 'note': ''})
    except Exception:
        _close(req_id, '실패 · 재개 오류', '재개 실패')
        raise
    res = out.get('result', {})
    status, event = (DONE, 'Slack 전송 완료') if res.get('ok') else (f"실패 · {res.get('error')}", f"전송 안 됨 · {res.get('error')}")
    _close(req_id, status, event)
    return {'req_id': req_id, 'status': status[:24], 'result': res}

def reject(*, req_id: str, approver_id: int, note: str, checkpointer) -> dict:
    row = _decide(req_id, approver_id, REJECTED, '반려', note)
    out = _resume(checkpointer, row.thread_id, {'approved': False, 'note': note})
    again = out['__interrupt__'][0].value['text'] if '__interrupt__' in out else None
    if again is not None:
        _close(req_id, WAITING, '재작성', text=again)
    return {'req_id': req_id, 'status': REJECTED if again is None else WAITING, 'text': again or row.payload['text']}