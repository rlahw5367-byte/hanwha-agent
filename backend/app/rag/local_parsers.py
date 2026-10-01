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


# HWPX 파싱해서 ParsedDoc 으로 리턴하는 함수 
def parse_hwpx(path: Path) -> ParsedDoc:
    import re
    import zipfile
    from xml.etree import ElementTree as ET

    ns_p = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
    blocks: list[ParsedBlock] = []

    tables = 0

    with zipfile.ZipFile(path) as zf:
        sections = sorted(n for n in zf.namelist() if re.match(r"Contents/section\d+\.xml$", n))
        for name in sections:
            root = ET.fromstring(zf.read(name))
            for para in root.findall(f"{ns_p}p"):
                # 표 처리 
                table_el = para.find(f".//{ns_p}tbl")
                if table_el is not None:
                    tables += 1 
                    rows: list[list[str]] = []
                    for tr in table_el.findall(f"{ns_p}tr"):
                        cells = []
                        for tc in tr.findall(f"{ns_p}tc"):
                            cells.append("".join(t.text or "" for t in tc.iter(f"{ns_p}t")).strip())
                        rows.append(cells)
                    if rows:
                        blocks.append(ParsedBlock("표", f"표{tables}", _table_to_markdown(rows[0], rows[1:])))
                    continue 
                # 문단 처리 
                text = "".join(t.text or "" for t in para.iter(f"{ns_p}t")).strip()
                if text:
                    blocks.append(ParsedBlock("조항", path.stem, text))

    return ParsedDoc(blocks=blocks, page_count=1, table_count=tables) 


# XSLX 파싱해 ParsedDoc으로 리턴하는 함수 
def parse_xlsx(path: Path) -> ParsedDoc:
    from openpyxl import load_workbook

    wb = load_workbook(str(path), data_only=True)
    blocks: list[ParsedBlock] = [] 

    for ws in wb.worksheets:
        rows = [
            ["" if c is None else str(c) for c in row]
            for row in ws.iter_rows(values_only=True)
            if any(c is not None for c in row)
        ]
        if not rows:
            continue
        blocks.append(
            ParsedBlock("표", ws.title, _table_to_markdown(rows[0], rows[1:]))
        )

    return ParsedDoc(blocks=blocks, page_count=len(wb.worksheets), table_count=len(blocks))


# PPTX 파싱해 ParsedDoc으로 리턴하는 함수 
def parse_pptx(path: Path) -> ParsedDoc:
    from pptx import Presentation

    prs = Presentation(str(path))
    blocks: list[ParsedBlock] = []

    for page_no, slide in enumerate(prs.slides, 1):
        lines = [shape.text.strip() for shape in slide.shapes
                 if shape.has_text_frame and shape.text.strip()]
        if slide.has_notes_slide:
            note = slide.notes_slide.notes_text_frame.text.strip() 
            if note:
                lines.append(f"[발표자 노트] {note}")
        if lines:
            blocks.append(ParsedBlock("조항", f"슬라이드 {page_no}", "\n".join(lines)))

    return ParsedDoc(blocks=blocks, page_count=len(prs.slides), table_count=0)

_CONVERT_HINT = {
    '.hwp': '한글에서 열고 [다른 이름으로 저장] → HWPX 또는 PDF 로 내보내세요. 구 .hwp 는 한컴 독자 바이너리라 열지 않고는 읽을 방법이 없습니다',
    '.doc': 'Word 에서 열고 .docx 로 저장하세요',
    '.ppt': 'PowerPoint 에서 열고 .pptx 로 저장하세요',
    '.xls': 'Excel 에서 열고 .xlsx 로 저장하세요',
    '.hwt': '한글 서식 파일입니다. 내용이 든 .hwpx 문서를 넣으세요',
    '.zip': '압축을 풀고 안의 문서를 한 건씩 넣으세요'
    }

HANDLERS = {
    '.docx': parse_docx, 
    '.pdf': parse_pdf, 
    '.hwpx': parse_hwpx,
    '.xlsx': parse_xlsx, 
    '.pptx': parse_pptx
}

def parse_local(path: str | Path) -> ParsedDoc | None:
    from app.core.exceptions import ValidationFailed
    p = Path(path)
    ext = p.suffix.lower()
    handler = HANDLERS.get(ext)
    if handler is None:
        if ext in _CONVERT_HINT:
            raise ValidationFailed(f'읽을 수 없는 형식입니다: {ext}', detail=_CONVERT_HINT[ext])
        raise ValidationFailed(f'지원하지 않는 형식입니다: {ext}', detail='핸들러를 추가하면 지원할 수 있습니다')
    try:
        doc = handler(p)
    except Exception as exc:
        log.warning('로컬 파싱 실패 (%s): %s', p.name, exc)
        return None
    if not doc.blocks:
        raise ValidationFailed(f'문서에서 글자를 찾지 못했습니다: {p.name}', detail='스캔본(이미지)일 수 있습니다. .env 의 UPSTAGE_PARSE_OCR 를 force 로 두고 실동작 모드로 다시 적재해 보세요')
    return doc