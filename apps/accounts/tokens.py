"""Emissão e validação dos tokens JWT (access + refresh) com PyJWT."""
import uuid
from datetime import datetime, timezone

import jwt
from django.conf import settings

ACCESS = "access"
REFRESH = "refresh"


class TokenError(Exception):
    """Token ausente, inválido, expirado ou do tipo errado."""

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


def _cfg() -> dict:
    return settings.JWT


def build_user_claims(user) -> dict:
    """Claims de negócio injetadas no access token (consumidas pelo Next.js)."""
    from apps.productions.services import productions_claims_for

    return {
        "user_id": str(user.pk),
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "productions": productions_claims_for(user),
    }


def _encode(payload: dict, lifetime) -> tuple[str, int]:
    cfg = _cfg()
    now = datetime.now(timezone.utc)
    exp = now + lifetime
    payload = {
        **payload,
        "iss": cfg["ISSUER"],
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": uuid.uuid4().hex,
    }
    token = jwt.encode(payload, cfg["SIGNING_KEY"], algorithm=cfg["ALGORITHM"])
    return token, int(lifetime.total_seconds())


def create_access_token(user) -> tuple[str, int]:
    claims = build_user_claims(user)
    return _encode({"token_type": ACCESS, "sub": str(user.pk), **claims}, _cfg()["ACCESS_TOKEN_LIFETIME"])


def create_refresh_token(user) -> str:
    token, _ = _encode({"token_type": REFRESH, "sub": str(user.pk)}, _cfg()["REFRESH_TOKEN_LIFETIME"])
    return token


def decode_token(token: str, expected_type: str) -> dict:
    cfg = _cfg()
    try:
        payload = jwt.decode(
            token,
            cfg["SIGNING_KEY"],
            algorithms=[cfg["ALGORITHM"]],
            issuer=cfg["ISSUER"],
            options={"require": ["exp", "iat", "sub", "token_type"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token expirado") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("Token inválido") from exc

    if payload.get("token_type") != expected_type:
        raise TokenError("Tipo de token inválido")
    return payload
