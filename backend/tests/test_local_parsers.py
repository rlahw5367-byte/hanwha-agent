# 로컬 파서 테스트 
from __future__ import annotations

from pathlib import Path
import pytest
from app.rag.local_parsers import parse_docx, parse_pdf

SAMPLES = Path(__file__).resolve().parents[2] / 'sandbox' / 'w5' / 'day01' / 'samples'

DOCX = SAMPLES / 'DOC-HR-014_국내출장_여비_규정_v2.0.docx' 
PDF = SAMPLES / 'DOC-HR-014_국내출장_여비_규정_v2.0.pdf'
SCANNED = SAMPLES / '_formats' / 'sample_scanned.pdf'

def _require(path: Path) -> None:
    if not path.is_file():
        pytest.skip(f"실습 재료가 없습니다: {path}")

def test_parse_docx_keeps_tables_in_body_order() -> None:
    _require(DOCX)
    doc = parse_docx(DOCX)
    assert len(doc.blocks) == 233 
    assert doc.table_count == 7 
    assert doc.page_count == 1 

    kinds = [block.kind for block in doc.blocks]
    assert kinds.count("표") == 7
    assert kinds[-1] == "조항"
    assert all(block.text.startswith("| ")  for block in doc.blocks if block.kind == "표")

def test_parse_pdf_counts_pages_and_reports_no_tables() -> None:
    _require(PDF)
    doc = parse_pdf(PDF)

    assert len(doc.blocks) == 16
    assert doc.page_count == 16
    assert doc.table_count == 0 
    assert [block.locator for block in doc.blocks[:3]] == ["p.1", "p.2", "p.3"]

def test_parse_pdf_returns_no_blocks_for_scanned_file() -> None:
    _require(SCANNED)
    doc = parse_pdf(SCANNED)

    assert doc.blocks == []
    assert doc.page_count == 1
    assert doc.table_count == 0 

