# 예외 처리

# 프로젝트 커스텀 예외의 부모
class AgentError(Exception):
    status_code = 400
    code = "agent_error"

    def __init__(self, message: str, *, detail: str | None = None):
        super().__init__(message)       # print(e) -> 메시지 나옴
        self.message = message
        self.detail = detail

# 요청한 자원이 없음
class NotFound(AgentError):
    status_code = 404
    code = "not_found_error"

# 자원은 있으나, 이 사용자가 접근할 수 없다.
class PermissionDenied(AgentError):
    status_code = 403
    code = "permission_denied"

# 입력값이 규칙에 맞지 않음
class ValidationFailed(AgentError):
    status_code = 422
    code = "validation_failed"

# 입력 가드에 걸림 - 길이 초과, 인젝션 의심 등
class GuardTripped(AgentError):
    status_code = 400
    code = "guard_tripped"

# 호출 한도 초과 시
class RateLimited(AgentError):
    status_code = 429
    code = "rate_limited"

# 승인없이 외부 실행 시도
class ApprovalRequired(AgentError):
    status_code = 409
    code = "approval_required"

# 모드 변경 불가 시
class ModeNotAvailable(AgentError):
    status_code = 409
    code = "mode_not_available"


# 외부 서비스 호출 실패
class ExternalServiceError(AgentError):
    status_code = 502
    code = "external_service_error"

# 로그인 실패, 누구인지 확인X
class AuthFailed(AgentError):
    status_code = 401
    code = "auth_failed"

    def __init__(self, message:str = "사번 또는 비밀번호가 올바르지 않습니다.", *, detail:str | None = None):
        super().__init__(message, detail=detail)
