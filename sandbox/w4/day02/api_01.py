import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend"))


import anthropic
from app.core.config import get_settings

settings = get_settings() 
key = settings.anthropic_api_key
if key is None:
    print(".env 의 앤트로픽 API 키가 비어있습니다. 확인해보세요.")
    sys.exit(1)

client = anthropic.Anthropic(api_key=key.get_secret_value())

response = client.messages.create(
    model=settings.llm_model, 
    max_tokens=settings.max_tokens, 
    messages=[
        {"role": "user", "content": "hello anthropic!! 오늘 서울 날씨 어때?"}
    ]
)
print(response.content[0].text)
