
from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Header
from app.api.v1.deps import CheckpointerDep
from app.core.exceptions import AuthFailed
from app.schemas.approval import ApprovalListOut, DecisionOut, RejectIn
from app.services import approval_service, auth_service
router = APIRouter(prefix='/approvals', tags=['approvals'])

def _approver_id(x_emp_no: str | None) -> int:
    if x_emp_no is None:
        raise AuthFailed('로그인이 필요합니다.')
    return auth_service.get_me(x_emp_no)['id']

@router.get('', response_model=ApprovalListOut)
def list_approvals() -> dict:
    return {'summary': approval_service.summary(), 'items': approval_service.list_waiting()}

@router.post('/{req_id}/approve', response_model=DecisionOut)
def approve(req_id: str, cp: CheckpointerDep, x_emp_no: Annotated[str | None, Header()]=None) -> dict:
    out = approval_service.approve(req_id=req_id, approver_id=_approver_id(x_emp_no), checkpointer=cp)
    result = out['result']
    message = 'Slack 으로 보냈습니다.' if result.get('ok') else f"보내지 못했습니다 — {result.get('error')}"
    return {'req_id': out['req_id'], 'status': out['status'], 'message': message}

@router.post('/{req_id}/reject', response_model=DecisionOut)
def reject(req_id: str, body: RejectIn, cp: CheckpointerDep, x_emp_no: Annotated[str | None, Header()]=None) -> dict:
    out = approval_service.reject(req_id=req_id, approver_id=_approver_id(x_emp_no), note=body.note, checkpointer=cp)
    message = '반려했습니다 — 사유를 반영한 문구로 다시 대기합니다.' if out['status'] == approval_service.WAITING else '반려했습니다.'
    return {'req_id': out['req_id'], 'status': out['status'], 'message': message}
