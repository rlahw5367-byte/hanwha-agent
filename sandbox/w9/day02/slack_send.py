from app.core.config import get_settings
from app.integrations.ports import SlackResult
from app.integrations.slack import SlackClient 

settings = get_settings() 
HAS_KEY = bool(settings.slack_bot_token and settings.slack_bot_token.get_secret_value())
TEXT = "사람이 직접 메세지 보내기"

if HAS_KEY:
    result = SlackClient().post(channel="", text=TEXT)
else:
    result = SlackResult(ok=True, channel=settings.slack_default_channel, ts="(미리 작성해둔 값)", simulate=True)

if result.simulated:
    route = "미리 작성해둔 값 - 보내지 않음"
elif result.ok:
    route = "내 토큰으로 보내기 - 내 채널 확인"
else: 
    route = "보내지 못함 - error 확인"

print("갈래 :", route)
print("ok   :", result.ok)
print("ts   :", bool(result.ts))
print("error:", result.error)
print("simulated:", result.simulated)