# 승인 서비스 
from __future__ import annotations

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.exceptions import ExternalServiceError, ModeNotAvailable, NotFound, PermissionDenied
from app.db.session import session_scope
from app.models import ApprovalRequest, AuditLog, User
from app.tools import registry
from datetime import datetime, date 
from sqlalchemy import select, func 

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
        if status == WAITING:
            row.approver_id, row.decided_at = None, None
        if text is not None:
            row.payload = {'text': text}
        s.add(AuditLog(approval_id=req_id, run_id=row.run_id, actor='시스템', event=event[:64]))


# 결정 처리 함수 
def _decide(req_id: str, approver_id: int, status: str, event: str, note: str='') -> ApprovalRequest:
    with session_scope() as s:
        row, user = (s.get(ApprovalRequest, req_id), s.get(User, approver_id))
        if row is None:
            raise NotFound(f'없는 승인 요청: {req_id}')
        if row.status != WAITING:
            raise PermissionDenied(f'이미 처리된 요청: {row.status}')
        if user is None or not user.can_approve:
            raise PermissionDenied('승인 권한이 없습니다')
        if row.requester_id == approver_id:       # 추가 
            raise PermissionDenied("자기 요청은 자기가 승인할 수 없습니다.")
        row.status, row.approver_id, row.decided_at = (status, approver_id, datetime.now())
        s.add(AuditLog(approval_id=req_id, run_id=row.run_id, actor=user.name, event=event, detail=note))
    return row

# 승인 기다리는 요청 목록 
def list_waiting() -> list[dict]:
    with session_scope() as s: 
        rows = s.execute(
            select(ApprovalRequest, User.name)
            .join(User, User.id == ApprovalRequest.requester_id)
            .where(ApprovalRequest.status == WAITING)
            .order_by(ApprovalRequest.requested_at)
        ).all() 
        items = [{"req_id": row.id, "text": row.payload["text"], "requester": name, 
                  "action_type": row.action_type, "status": row.status, 
                  "requested_at": row.requested_at} for row, name in rows]
    for item in items:
        item["events"] = events(item["req_id"])
    return items
    

def summary() -> dict:
    today = date.today()
    with session_scope() as s:
        waiting = s.scalar(select(func.count()).select_from(ApprovalRequest).where(ApprovalRequest.status == WAITING))
        decided = s.execute(select(ApprovalRequest.status, ApprovalRequest.requested_at, ApprovalRequest.decided_at)
                            .where(ApprovalRequest.status != WAITING, ApprovalRequest.decided_at.is_not(None), 
                                   func.date(ApprovalRequest.decided_at) == today)).all()
    minutes = [int((row.decided_at - row.requested_at).total_seconds() // 60) for row in decided]
    return {'waiting': waiting, 'approved_today': sum((1 for row in decided if row.status == DONE)), 
            'rejected_today': sum((1 for row in decided if row.status == REJECTED)), 
            'avg_minutes': round(sum(minutes) / len(minutes)) if minutes else None}


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

# 승인 반려 처리 (메인 함수)
def reject(*, req_id: str, approver_id: int, note: str, checkpointer) -> dict:
    row = _decide(req_id, approver_id, REJECTED, '반려', note)
    try:
        out = _resume(checkpointer, row.thread_id, {'approved': False, 'note': note})
    except Exception:
        _close(req_id, "실패, 재개 오류", "재개 실패")
        raise
    again = out['__interrupt__'][0].value['text'] if '__interrupt__' in out else None
    if again is not None:
        _close(req_id, WAITING, '재작성', text=again)
    return {'req_id': req_id, 'status': REJECTED if again is None else WAITING, 'text': again or row.payload['text']}