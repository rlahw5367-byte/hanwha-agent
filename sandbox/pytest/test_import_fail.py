from app.core.config import get_settings

def test_설정_불러오기():
    assert get_settings().app_mode == "mock"