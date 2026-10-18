from typing import Any, Optional


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}


class AuthenticationError(AppException):
    def __init__(self, message: str = "Invalid or missing authentication token"):
        super().__init__(message=message, status_code=401)


class AuthorizationError(AppException):
    def __init__(self, message: str = "You do not have permission to access this resource"):
        super().__init__(message=message, status_code=403)


class ResourceNotFoundError(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404)


class PlanValidationError(AppException):
    def __init__(self, message: str = "Plan validation failed", detail: Optional[Any] = None):
        super().__init__(message=message, status_code=422, detail=detail)


class ToolExecutionError(AppException):
    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(message=message, status_code=500, detail=detail)


class WorkflowConflictError(AppException):
    def __init__(self, message: str = "Workflow state conflict"):
        super().__init__(message=message, status_code=409)


class CloudLLMError(AppException):
    def __init__(self, message: str = "Cloud LLM service error", detail: Optional[Any] = None):
        super().__init__(message=message, status_code=502, detail=detail)
