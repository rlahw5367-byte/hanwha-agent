import pytest


@pytest.fixture
def travel_doc() -> dict:
    return {
        "doc_id": "DOC-HR-014",
        "title": "국내출장 여비 규정",
        "dept": "인사",
        "version": "v2.0",
        "security_level": "일반",
        "file_format": "docx",
        "status": "현행",
    }