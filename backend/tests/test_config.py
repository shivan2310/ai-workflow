import pytest
from app.core.config import Settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    PlanValidationError,
    ToolExecutionError,
    WorkflowConflictError,
    CloudLLMError,
)


def test_settings_defaults():
    settings = Settings()
    assert settings.APP_NAME == "AutoPilot AI"
    assert settings.LLM_MODEL == "gpt-oss-120b"
    assert settings.API_PREFIX == "/api"
    assert "jwks.json" in settings.jwks_url
    assert "/auth/v1" in settings.jwt_issuer


def test_settings_custom_overrides():
    custom = Settings(
        APP_NAME="Custom AutoPilot",
        LLM_MODEL="gpt-oss-custom",
        SUPABASE_URL="https://custom.supabase.co",
    )
    assert custom.APP_NAME == "Custom AutoPilot"
    assert custom.LLM_MODEL == "gpt-oss-custom"
    assert custom.jwks_url == "https://custom.supabase.co/auth/v1/.well-known/jwks.json"
    assert custom.jwt_issuer == "https://custom.supabase.co/auth/v1"


def test_exceptions_status_codes():
    assert AuthenticationError().status_code == 401
    assert AuthorizationError().status_code == 403
    assert ResourceNotFoundError().status_code == 404
    assert PlanValidationError().status_code == 422
    assert ToolExecutionError("fail").status_code == 500
    assert WorkflowConflictError().status_code == 409
    assert CloudLLMError().status_code == 502
