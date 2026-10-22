from .calculator import add, substact

def test_add():
    result = add(10, 20)
    assert result == 30  # 검사 명령어 

def test_substract():
    result = substact(10, 3)
    assert result == 7


