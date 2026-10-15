import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import get_settings
from app.integrations.factory import get_llm
from app.integrations.ports import LLMResult
from app.rag.retriever import expand_queries 


# 질문 
QUESTIONS = ["출장비 얼마까지 나오나요?", "숙박 기준 알려주세요", "재택은 주 며칠까지 되나요?"]

# API 키 없는 경우 미리 뽑아둔 재작성 결과
CANNED = {
    "출장비 얼마까지 나오나요?": "국내출장 여비 지급 상한\n일비 숙박비 식비 기준액",
    "숙박 기준 알려주세요": "숙박비 상한 기준\n출장 숙박비 지급 기준표",
    "재택은 주 며칠까지 되나요?": "재택근무 주당 허용 일수\n재택근무 운영 지침 신청 기준",
}

REWRITE_SYSTEM = (
    "당신은 사내 규정 검색에 쓸 질의를 고쳐 쓰는 도우미입니다.\n"
    "사용자의 질문에 답하지 않습니다. 근거 문서는 필요없습니다. - "
    "규정 내용을 말하는 것이 아니라 검색창에 넣을 문장을 만드는 일입니다.\n"
    "같은 뜻을 사내 규정에서 사용할 법한 용어로 바꾼 짧은 검색 질의 3개를 만듭니다.\n"
    "- 한 줄에 질의 하나씩, 번호-기호-설명 없이 작성한다.\n"
    "- 각 질의는 20자 안팎의 명사구로 작성한다.\n"
    "- 금액,일수 같은 숫자는 지어내지 않는다."
)


class StubRewriter:

    def _call(self, system: str, user_text: str) -> tuple[str, dict, int]:
        return CANNED.get(user_text, user_text), {}, 0


settings = get_settings() 
llm, mode = (get_llm(), "live") if settings.is_live else (StubRewriter(), "mock")
print(f"모드: {mode}\n")

rule_total = llm_total = 0 
for i, q in enumerate(QUESTIONS, 1):
    rule = expand_queries(q, settings.multi_query_n)

    text, _, _ = llm._call(REWRITE_SYSTEM, q)

    made = [ln.strip() for ln in text.splitlines() if ln.strip()]
    rule_total, llm_total = rule_total + len(rule), llm_total + len(made)
    print(f'[{i}] "{q}"')
    print(f" 규칙 기반 {len(rule)}갈래 : " + " / ".join(rule))
    print(f" 재작성 {len(made)}갈래 : " + " / ".join(made))

n = len(QUESTIONS)
print(f"\n규칙 기반 평균 {rule_total / n:.1f}갈래. 재작성 평균 {llm_total / n:.1f}갈래")