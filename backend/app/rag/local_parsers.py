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


# DOCX를 본문 순서 그대로 읽어 ParsedDoc 으로 리턴하는 함수 
def parse_docx(path: Path) -> ParsedDoc:
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    doc = Document(str(path))
    blocks: list[ParsedBlock] = []
    tables = 0 

    body = doc.element.body
    for child in body.iterchildren():
        tag = child.tag.split("}")[-1] # p or tbl 
        if tag == "p":
            text = Paragraph(child, doc).text.strip() 
            if text:
                blocks.append(ParsedBlock("조항", f"{path.stem}", text))
        elif tag == "tbl":
            table = Table(child, doc)
            rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
            if not rows:
                continue
            tables += 1 
            blocks.append(
                ParsedBlock("표", f"표{tables}", _table_to_markdown(rows[0], rows[1:]))   # 수정 
            )

    return ParsedDoc(blocks=blocks, page_count=1, table_count=tables) 


# 표의 머리글과 나머지 행들을 마크다운 표 한 덩어리로 변경하는 함수 : 추가 
def _table_to_markdown(headers: list[str], rows: list[list[str]]) -> str:
    # headers : 표의 첫줄(제목줄)
    # rows : 표의 실제 데이터들 
    head = '| ' + ' | '.join(headers) + ' |'
    sep = '|' + '---|' * len(headers)
    body = ['| ' + ' | '.join((str(c) for c in r)) + ' |' for r in rows]
    return '\n'.join([head, sep, *body])