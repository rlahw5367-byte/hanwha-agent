import sys
from pathlib import Path

# backend 폴더를 모듈 검색 경로로 잡아주기 
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend")) 

import anthropic

from app.core.config import get_settings

# 설정 정보에서 API 키값 가져오기 
settings = get_settings()
key = settings.anthropic_api_key  
if key is None: # 키가 없으면 
    print(".env 의 anthropic_api_key 가 비어있습니다. 확인해주세요.")
    sys.exit(1) # 프로그램 종료 

# API 요청하는 클라이언트 생성 : api key 인자로 전달 
client = anthropic.Anthropic(api_key=key.get_secret_value()) # pydantic SecretStr 타입이 주는 메서드 

# 메세지 생성하여 요청 : 인자 값들을 .env에 지정된 값을 가져와 사용하도록 구성 (AI-Native 아키텍처 설계 방침)
response = client.messages.create(
    model=settings.llm_model,
    max_tokens=settings.max_tokens, 
    system="너는 사내 규정 질의 응답 도우미다. 근거가 없으면 없다고 말해야해.", 
    messages=[
        {"role": "user", "content": "제주도 출장 숙박비 한도가 얼마인가요?"}
    ],
) 
 
print(response)
print("".join(b.text for b in response.content if b.type == "text"))
print("입력 토큰:", response.usage.input_tokens, ", 출력 토큰:", response.usage.output_tokens)
