from typing import Optional
from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_supabase_token
from app.core.exceptions import AuthenticationError
from app.schemas.auth import AuthenticatedUser
from app.db.database import get_db

http_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
) -> AuthenticatedUser:
    """FastAPI dependency to extract and verify Supabase JWT from Authorization header."""
    if not credentials or not credentials.credentials:
        raise AuthenticationError("Authorization Bearer token is required")

    return verify_supabase_token(credentials.credentials)

