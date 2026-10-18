import uuid
import time
import pytest
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from app.core.security import verify_supabase_token
from app.core.exceptions import AuthenticationError
from app.core.config import get_settings


@pytest.fixture(autouse=True)
def configure_secret(monkeypatch):
    monkeypatch.setattr(get_settings(), "SUPABASE_JWT_SECRET", "super-secret-test-key-32-bytes-long!")
    monkeypatch.setattr(get_settings(), "SUPABASE_JWT_AUDIENCE", "authenticated")


def test_empty_or_whitespace_token():
    with pytest.raises(AuthenticationError, match="cannot be empty"):
        verify_supabase_token("")
    with pytest.raises(AuthenticationError, match="cannot be empty"):
        verify_supabase_token("   ")


def test_invalid_token_format():
    with pytest.raises(AuthenticationError, match="Invalid authentication token"):
        verify_supabase_token("not-a-valid-jwt-token")


def test_expired_token():
    user_id = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "aud": "authenticated",
        "exp": int(time.time()) - 100,  # Expired
    }
    token = jwt.encode(payload, "super-secret-test-key-32-bytes-long!", algorithm="HS256")

    with pytest.raises(AuthenticationError, match="has expired"):
        verify_supabase_token(token)


def test_audience_mismatch():
    user_id = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "aud": "wrong-audience",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, "super-secret-test-key-32-bytes-long!", algorithm="HS256")

    with pytest.raises(AuthenticationError, match="Invalid authentication token"):
        verify_supabase_token(token)


def test_missing_sub_claim():
    payload = {
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, "super-secret-test-key-32-bytes-long!", algorithm="HS256")

    with pytest.raises(AuthenticationError, match="missing 'sub'"):
        verify_supabase_token(token)


def test_invalid_uuid_sub_claim():
    payload = {
        "sub": "not-a-uuid",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, "super-secret-test-key-32-bytes-long!", algorithm="HS256")

    with pytest.raises(AuthenticationError, match="not a valid UUID"):
        verify_supabase_token(token)


def test_valid_token_success():
    expected_uuid = uuid.uuid4()
    payload = {
        "sub": str(expected_uuid),
        "email": "student@innotech.org",
        "role": "authenticated",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, "super-secret-test-key-32-bytes-long!", algorithm="HS256")

    user = verify_supabase_token(token)
    assert user.id == expected_uuid
    assert user.email == "student@innotech.org"
    assert user.role == "authenticated"


def test_wrong_signature_secret():
    user_id = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    # Sign with a different secret
    token = jwt.encode(payload, "wrong-secret-key-1234567890123456", algorithm="HS256")

    with pytest.raises(AuthenticationError, match="Signature verification failed"):
        verify_supabase_token(token)
