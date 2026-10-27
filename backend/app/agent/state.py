# 그래프 상태 

import operator
from typing import Annotated, TypedDict

# 질문 하나가 그래프를 한 바퀴 도는 동안의 상태 
class WorkflowState(TypedDict, total=False):
    question: str                 # 질문 (입력)
    user: dict                    # 사용자 (입력)
    sources: list[dict]           # search가 사용 
    passed: bool                  # 갈래를 고르는 값 
    versions: dict                # found, insufficient가 사용 
    note: str                     # insufficient가 사용
    trace: Annotated[list[str], operator.add]   

# *추가 
class LoopState(WorkflowState, total=False):
    query: str   # 고친 질문 (원 질문은 question)
    fixes: int   # 몇번 고쳤는지 

# 승인 그래프 상태 
class ApprovalState(TypedDict, total=False):
    text: str       # 보낼 문구 (draft 가 사용)
    decision: dict  # 재개할때 인자 값 (gate 사용)
    result: dict    # 전송 결과 (send가 사용)
    rewrites: int   # 재 작성 카운트 (반려 루프)

# Supervisor 그래프 상태 
class SupervisorState(WorkflowState, total=False):
    next: str
    turns: int
    draft: dict
    run_id: str