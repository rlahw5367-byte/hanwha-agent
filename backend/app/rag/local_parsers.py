from __future__ import annotations

from pathlib import Path
from app.core.logging import get_logger
from app.integrations.ports import ParsedBlock, ParsedDoc

log = get_logger(__name__)

# PDF 파서 함수 : 페이지 단위로 읽어 ParsedDoc으로 리턴 
def parse_pdf(path: Path) -> ParsedDoc:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    blocks: list[ParsedBlock] = [] 

    for page_no, page in enumerate(reader.pages, 1):
        text = (page.extract_text() or "").strip() 
        if not text:
            log.info("텍스트 없음 (스캔본으로 보임): %s p.%d", path.name, page_no)
            continue
        blocks.append(ParsedBlock("조항", f"p.{page_no}", text))

    return ParsedDoc(blocks=blocks, page_count=len(reader.pages), table_count=0)


