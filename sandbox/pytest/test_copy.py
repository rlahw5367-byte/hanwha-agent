#sandbox/pytest/test_copy.py

def test_제목이_있다():
    문서 = {"doc_id": "DOC-HR-014", "title": "국내출장 여비 규정", "security_level": "일반"}
    assert 문서["title"]


def test_보안등급이_세_값_중_하나다():
    문서 = {"doc_id": "DOC-HR-014", "title": "국내출장 여비 규정", "security_level": "일반"}
    assert 문서["security_level"] in ("일반", "3급", "대외비")


def test_문서번호_형식이_맞다():
    문서 = {"doc_id": "DOC-HR-014", "title": "국내출장 여비 규정", "security_level": "일반"}
    assert 문서["doc_id"].startswith("DOC-")