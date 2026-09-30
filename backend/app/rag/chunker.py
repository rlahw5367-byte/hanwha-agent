from __future__ import annotations

import re
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.integrations.ports import ParsedDoc

# 제1조, 제12조(숙박비), 별표1 .. 
_ARTICLE = re.compile(r"(제\s*\d+\s*조(?:의\s*\d+)?\s*(?:\([^)]{1,30}\))?)")
_ANNEX = re.compile(r"(별표\s*\d+)")

MAX_CHARS = 1200
MIN_CHARS = 30
TOC_BODY_MIN = 10   

@dataclass
class ChunkDraft:
    kind: str      # 조항 | 표 
    locator: str
    text: str

# 조 단위로 자르기
def _split_articles(text: str) -> list[tuple[str, str]]:
    parts = _ARTICLE.split(text)
    if len(parts) <= 1:
        return [("", text.strip())] if text.strip() else [] 

    out: list[tuple[str, str]] = []
    head = parts[0].strip() 
    if len(head) >= MIN_CHARS:
        out.append(("", head))
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        body = parts[i+1].strip() if i + 1 < len(parts) else "" 
        out.append((title, f"{title} {body}".strip()))

    return out 


# 길이가 아주 긴 조를 limit 이하로 나누기 (폴백)
def _hard_wrap(text: str, limit: int = MAX_CHARS) -> list[str]:
    if len(text) <= limit:
        return [text]
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=limit, 
        chunk_overlap=0, 
        separators=["\n\n", "\n", "다. ", ". ", " ", ""],
        keep_separator="end"
    )
    return splitter.split_text(text)  

# ParsedDoc -> 청크 목록으로 변환해서 리턴
def chunk(doc: ParsedDoc) -> list[ChunkDraft]:
    out: list[ChunkDraft] = []
    buffer: list[str] = []
    buffer_locator = ""

    def flush() -> None:
        nonlocal buffer, buffer_locator
        if not buffer:
            return
        out.extend(_articles_from("/n".join(buffer), buffer_locator))
        buffer = []
        buffer_locator = ""

    for block in doc.blocks:
        if block.kind == "표":
            flush()
            out.append(ChunkDraft("표", block.locator, block.text))
            continue
        if not buffer_locator:
            buffer_locator = block.locator
        buffer.append(block.text)
    
    flush()
    return out

# 본문 덩어리를 조 단위로 자르는 함수
def _article_from(text: str, fallback_locator: str) -> list[ChunkDraft]:
    drafts: list[ChunkDraft] = []
    for title, body, in _split_articles(text):
        if not body.strip():
            continue

        remainder = body[len(title):].strip() if title else body
        if len(remainder) < TOC_BODY_MIN:
            if drafts:
                drafts[-1].text += "\n" + body
            else:
                drafts.append(ChunkDraft("조항", fallback_locator, body))
            continue

        if not title:
            locator = fallback_locator
        else:
            annex = _ANNEX.search(body)
            locator = title if not annex else f"{title} - {annex.group(1)}"

        