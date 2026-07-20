"""Supabase JWT authentication for the student-section API.

The API never accepts a user ID header. A browser identity is derived only from
a verified Supabase access token, and failures are deliberately non-specific.
"""
from __future__ import annotations

from functools import lru_cache
from uuid import UUID

import jwt
from fastapi import Header, HTTPException, status
from jwt import PyJWKClient

from app.core.config import settings


@lru_cache
def _jwk_client(url: str) -> PyJWKClient:
    return PyJWKClient(f"{url.rstrip('/')}/auth/v1/.well-known/jwks.json", cache_keys=True)


def authenticated_supabase_user(authorization: str | None = Header(default=None)) -> tuple[UUID, str]:
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="La sección de estudiantes todavía no está configurada.")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Necesitas iniciar sesión para continuar.")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        signing_key = _jwk_client(settings.supabase_url).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience=settings.supabase_jwt_audience,
            issuer=settings.supabase_jwt_issuer or f"{settings.supabase_url.rstrip('/')}/auth/v1",
        )
        return UUID(str(claims["sub"])), token
    except Exception as error:
        # Never echo a token, upstream auth detail, or a key in an API response.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tu sesión no pudo verificarse. Inicia sesión nuevamente.") from error
