# 외부 연동 Protocol : 규격 
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

# LLM 호출 한번의 결과 
@dataclass
class LLMResult:
    text: str
    model: str
    input_tok: int = 0
    cache_tok: int = 0
    output_tok: int = 0 
    cost_krw: float = 0.0
    latency_ms: int = 0 
    extras: dict = field(default_factory=dict) # 화면에 필요한 여분 데이터를 실어 보내기 

# LLM 어댑터가 지켜야할 규칙 (인터페이스,코드 규격)
@runtime_checkable
class LLMPort(Protocol):
    def answer(self, *, question: str, contexts: list[dict], user: dict) -> LLMResult: ...

#----------- 문서 파싱 결과 -----------------------------------------------
# 파싱 결과의 최소 단위. 문서를 잘라놓은 덩어리 하나 : PDF, DOCX, HWPX  
@dataclass
class ParsedBlock: 
    kind: str            # 덩어리 종류 : 조항, 표 
    locator: str         # 원본 어디서 나온 덩어리 인지  : p.6, 표2
    text: str            # 덩어리 글자들 

# 문서 한건을 파싱한 결과 전체 
@dataclass
class ParsedDoc: 
    blocks: list[ParsedBlock] = field(default_factory=list)  # 본문에 놓은 순서 그대로 덩어리 목록 저장 
    page_count: int = 0                                      # 페이지 수. 페이지 개념이 없는 docx형식은 1로 둔다 .
    table_count: int = 0                                     # 표를 몇개 알아봤는지. 

# 파서 어댑터가 지켜야할 규칙 : 로컬 파서 또는 파싱 API 를 사용해도 아래 모양만 맞춰주면, 같은 코드로 사용가능하게 해줌 
@runtime_checkable
class ParserPort(Protocol):
    def parse(self, path: str) -> ParsedDoc: ... 