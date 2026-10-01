# 파싱 진입점  
from __future__ import annotations

from pathlib import Path

from app.integrations.ports import ParsedBlock, ParsedDoc
from app.rag.local_parsers import parse_local

_PLAIN = {".txt", ".md"}         # 파싱 X. 파일 열어 바로 읽기 
_HTML = {".html", ".htm"}        # 태그를 걷어내야 글자가 남는 형식
_LOCAL_ONLY = {".hwp", ".hwpx"}  # 상용파서에 보내지 않을 형식 

# 파일 한건을 읽어, 형식과 무관한 한가지 모양(ParsedDoc) 형태로 리턴해주는 함수 
def parse(path: str | Path, *, use_upstage: bool = False) -> ParsedDoc:
    p = Path(path)
    ext = p.suffix.lower()
    if ext in _PLAIN:
        return _parse_plain(p)
    if ext in _HTML:
        return _parse_html(p)
    if use_upstage and ext not in _LOCAL_ONLY:
        from app.integrations.upstage import UpstageParser
        return UpstageParser().parse(str(p))
    return parse_local(p)

def _parse_plain(p: Path) -> ParsedDoc:
    text = p.read_text(encoding="utf-8", errors="replace")
    blocks = [
        ParsedBlock("조항", f"{p.name} {i + 1}단락", part.strip()) 
        for i, part in enumerate(text.split("\n\n")) 
        if part.strip()
    ]
    return ParsedDoc(blocks=blocks, page_count=1, table_count=0)

def _parse_html(p: Path) -> ParsedDoc:
    import re
    raw = p.read_text(encoding="utf-8", errors="replace")
    # <style> <script> 태그 제외 
    raw = re.sub('<(script|style)[^>]*>.*?</\\1>', ' ', raw, flags=re.S | re.I)
    # 테이블 태그 모아놓기 
    tables = re.findall('<table.*?</table>', raw, flags=re.S | re.I)
    body = re.sub('<table.*?</table>', ' ', raw, flags=re.S | re.I)
    # 본문에서 태그 제외 (TODO title 태그 -> 제외)
    body = re.sub('\\s+', ' ', re.sub('<[^>]+>', ' ', body)).strip()

    blocks = [ParsedBlock("조항", p.name, body)] if body else []
    for i, table in enumerate(tables, 1):
        cleaned = re.sub('\\s+', ' ', re.sub('<[^>]+>', ' ', table)).strip()
        blocks.append(('표', f'{p.name} · 표{i}', cleaned))

    return ParsedDoc(blocks=blocks, page_count=1, table_count=len(tables))