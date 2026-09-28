def clean_title(raw):
    return raw.strip()

def test_앞뒤_공백을_지운다():
    assert clean_title("    hello pytest    ") == "hello pytest"

def test_공백이_없으면_그대로다():
    assert clean_title("안녕 테스트야") == "안녕 테스트야"

def 빈_제목이면_빈_문자열():
    assert clean_title("  ") == ""