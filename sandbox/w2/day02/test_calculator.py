from calculator import add, sub

def test_add():
    result = add(10, 20)
    assert result == 30

def test_sub():
    result = sub(10, 3)
    assert result == 7