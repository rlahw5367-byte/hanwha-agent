from __future__ import annotations

from html import escape
import streamlit as st

from core import api_client, router, session
from ui.badge import badge_html
from ui.card import card, page_header
from ui.chart import timeline
from ui.status import progress

DEFAULT_DOC = "DOC-HR-014"

def render() -> None:
    doc_id = st.session_state.get("selected_doc", DEFAULT_DOC)

    if st.button("← 문서 관리", key="back_docs"):
        router.go("documents")     

    try:
        doc = api_client.get_document(doc_id, emp_no=session.emp_no())
        versions = api_client.list_versions(doc_id, emp_no=session.emp_no())
    except api_client.ApiError as exc:
        st.error(str(exc))
        return

    page_header(
        doc["title"],
        crumb=f"문서 관리 › {doc['doc_id']}",
        subtitle=f"{doc['dept']} · 보안등급 {doc['security_level']} · {doc['file_format'].upper()}",
        badges=[(f"현행 {doc['version']}", "ok")],
    )

    left, right = st.columns([2.1, 1])
    with left:
        _version_timeline(versions)
    with right:
        _policy_card()
        _actions(doc["doc_id"], doc["version"])



# 버전 하나를 타임라인 항목 하나로 만들어주는 함수 
def _version_block(v: dict) -> str: 
    label = "현행 · 검색 대상" if v["searchable"] else f"{v['status']} · 검색 제외"
    tone = "ok" if v["searchable"] else "neutral"
    detail = " · ".join(x for x in [
        v["period"],
        v["embed_model"] or "임베딩 모델 미기록",
        f"임베딩 완료 {v['indexed_at']}" if v["indexed_at"] else "임베딩 이력 없음",
    ] if x)
    return (
        '<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">'
        f'<span style="font-weight:700;font-size:var(--ag-fs-lg)">{escape(v["version"])}</span>'
        f'{badge_html(label, tone)}'
        f'<span style="color:var(--ag-muted);font-size:var(--ag-fs-xs)">'
        f'청크 {v["chunk_count"]} · 검색 반영 {escape(v["index_status"])}</span></div>'
        f'<div class="ag-src-meta">{escape(detail)}</div>'
    )
