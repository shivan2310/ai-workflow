import uuid
from typing import Optional, Dict, Any
import jwt
from jwt import PyJWKClient, PyJWTError, ExpiredSignatureError, InvalidTokenError
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.schemas.auth import AuthenticatedUser

settings = get_settings()

_jwk_client: Optional[PyJWKClient] = None


def get_jwk_client() -> PyJWKClient:
    global _jwk_client
    if _jwk_client is None:
        _jwk_client = PyJWKClient(settings.jwks_url, cache_jwk_set=True, lifespan=3600)
    return _jwk_client


def verify_supabase_token(token: str) -> AuthenticatedUser:
    """
    Validate a Supabase access token (JWT) using asymmetric JWKS or secret fallback.
    Validates expiration, audience, issuer (if applicable), and extracts the user UUID.
    """
    if not token or not token.strip():
        raise AuthenticationError("Bearer token cannot be empty")

    try:
        # Inspect unverified header to see algorithm and key ID
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg", "HS256")

        decode_kwargs: Dict[str, Any] = {
            "algorithms": ["RS256", "ES256", "HS256"],
            "options": {
                "verify_exp": True,
                "verify_aud": bool(settings.SUPABASE_JWT_AUDIENCE),
                "verify_signature": True,
            },
        }
        if settings.SUPABASE_JWT_AUDIENCE:
            decode_kwargs["audience"] = settings.SUPABASE_JWT_AUDIENCE

        payload: Dict[str, Any]

        # Case 1: Asymmetric token with kid (standard modern Supabase JWKS)
        if alg in ["RS256", "ES256"] and "kid" in unverified_header:
            try:
                jwk_client = get_jwk_client()
                signing_key = jwk_client.get_signing_key_from_jwt(token)
                payload = jwt.decode(token, signing_key.key, **decode_kwargs)
            except Exception as jwk_err:
                raise AuthenticationError(f"JWKS key resolution failed: {str(jwk_err)}")

        # Case 2: Shared secret key (HS256 / legacy Supabase or local test setup)
        elif settings.SUPABASE_JWT_SECRET:
            payload = jwt.decode(token, settings.SUPABASE_JWT_SECRET, **decode_kwargs)

        # Case 3: If no secret key is provided and no kid found, try JWKS or reject
        else:
            raise AuthenticationError(
                "Unable to verify token: No JWKS key ID found in header and no SUPABASE_JWT_SECRET configured"
            )

        # Validate subject (user ID)
        sub = payload.get("sub")
        if not sub:
            raise AuthenticationError("Token payload missing 'sub' (user ID) claim")

        try:
            user_uuid = uuid.UUID(str(sub))
        except (ValueError, TypeError):
            raise AuthenticationError("Token 'sub' claim is not a valid UUID")

        return AuthenticatedUser(
            id=user_uuid,
            email=payload.get("email"),
            role=payload.get("role"),
            aud=payload.get("aud"),
        )

    except ExpiredSignatureError:
        raise AuthenticationError("Authentication token has expired")
    except (InvalidTokenError, PyJWTError) as err:
        raise AuthenticationError(f"Invalid authentication token: {str(err)}")
    except AuthenticationError:
        raise
    except Exception as err:
        raise AuthenticationError(f"Token validation failed: {str(err)}")
