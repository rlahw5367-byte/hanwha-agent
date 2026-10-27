from collections.abc import Callable

from langgraph.graph import END, START, StateGraph

from app.agent.patterns import Step
from app.agent.state import WorkflowState


'''
START -> search -> pick(state) ----- "found"          -> found        -> END 
                                |
                                ---- "insufficient"   -> insufficient -> END

'''
# search -> (pick이 고른 갈래) -> END  
def build_graph(search: Step, routes: dict[str, Step], pick: Callable[[dict], str]):
    g = StateGraph(WorkflowState) # 상태 선언 
    g.add_node("search", search)  # 첫 단계 노드로 등록 : 검색 
    for name, step in routes.items(): # 분기별 노트 등록, 각 노드는 END로 가는 선을 이어주기 
        g.add_node(name, step)
        g.add_edge(name, END)
    g.add_edge(START, "search") # 시작 -> search 실행 
    g.add_conditional_edges("search", pick, {name: name for name in routes})
    return g.compile() # 그래프 생성 

# 되돌아가는 선 추가 
from langgraph.types import RetryPolicy
from app.agent.state import LoopState

def build_loop_graph(search: Step, fix: Step, routes: dict[str, Step], pick: Callable[[dict], str], *, 
                     search_retry: RetryPolicy | None = None, fix_retry: RetryPolicy | None = None,
                     checkpointer=None): # 추가 

    g = StateGraph(LoopState)
    g.add_node("search", search, retry_policy=search_retry)
    g.add_node("fix", fix, retry_policy=fix_retry)
    for name, step in routes.items():
        g.add_node(name, step)
        g.add_edge(name, END)

    g.add_edge(START, "search")
    g.add_conditional_edges("search", pick, {"fix": "fix", **{name: name for name in routes}})
    g.add_edge("fix", "search")
    return g.compile(checkpointer=checkpointer)   # 수정 

# 승인 그래프, 게이트 
from langgraph.types import interrupt
from app.agent.state import ApprovalState
MAX_REWRITES = 2

# 사람의 결정을 기다리게 하는 함수 
def _gate(state: dict) -> dict: 
    return {"decision": interrupt({"text": state["text"]})}

# 승인 그래프 : draft -> gate(멈춤) -> 승인이면 send ->  END 
def build_approval_graph(draft: Step, send: Step, *, checkpointer, rewrite: Step | None = None):
    if checkpointer is None: 
        raise ValueError("승인 그래프는 저장소가 있어야 멈췄다 이어 간다. checkpointer를 넘기세요.")

    g = StateGraph(ApprovalState)
    g.add_node("draft", draft)
    g.add_node("gate", _gate)
    g.add_node("send", send)

    g.add_edge(START, "draft")
    g.add_edge("draft", "gate")

    def pick(state: dict) -> str:
        if state["decision"].get("approved"): 
            return "send"
        return "rewrite" if rewrite is not None and state.get("rewrites", 0) < MAX_REWRITES else "end"

    routes = {"send": "send", "end": END}
    if rewrite is not None:
        g.add_node("rewrite", rewrite)
        g.add_edge("rewrite", "gate")
        routes["rewrite"] = "rewrite"
        
    g.add_conditional_edges("gate", pick, routes)
    g.add_edge("send", END)

    return g.compile(checkpointer=checkpointer)


# supervisor : 다음 노드를 고르는 수퍼바이저 노드 
from app.agent.state import SupervisorState

def build_supervisor_graph(workers: dict[str, str], pick: Callable[[dict], str]):
    def supervisor(state: dict) -> dict: 
        return {"next": pick(state), "turns": state.get("turns", 0) + 1}

    g = StateGraph(SupervisorState)
    g.add_node("supervisor", supervisor)
    for name, step in workers.items(): 
        g.add_node(name, step)
        g.add_edge(name, "supervisor")
    
    g.add_edge(START, "supervisor")
    g.add_conditional_edges("supervisor", lambda s: s["next"], {**{n: n for n in workers}, "finish": END})
    return g.compile() 
