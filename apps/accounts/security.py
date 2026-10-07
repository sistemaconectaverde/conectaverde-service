"""Autenticação Bearer JWT e controle de acesso por perfil (RBAC)."""
from functools import wraps
from typing import Callable

from django.contrib.auth import get_user_model
from ninja.errors import HttpError
from ninja.security import HttpBearer

from apps.accounts.tokens import ACCESS, TokenError, decode_token
from apps.core.choices import Role


class JWTAuth(HttpBearer):
    """Valida o header `Authorization: Bearer <access>` e coloca o usuário em request.auth."""

    openapi_bearerFormat = "JWT"

    def authenticate(self, request, token):
        try:
            payload = decode_token(token, ACCESS)
        except TokenError as exc:
            # 401 com detalhe -> o front sabe que deve chamar /api/auth/token/refresh/ (CT-07)
            raise HttpError(401, exc.detail) from exc

        User = get_user_model()
        user = User.objects.filter(pk=payload["sub"], is_active=True).first()
        if user is None:
            raise HttpError(401, "Usuário inativo ou inexistente")

        request.jwt_claims = payload
        return user


def roles_allowed(*roles: str) -> Callable:
    """
    Restringe um endpoint a perfis específicos. Use ABAIXO do decorator do router:

        @router.get("/algo/")
        @roles_allowed(Role.ADMIN, Role.CONSULTOR)
        def view(request): ...
    """
    allowed = {Role(r) for r in roles}

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            user = getattr(request, "auth", None)
            if user is None or not getattr(user, "is_authenticated", False):
                raise HttpError(401, "Não autenticado")
            if user.role not in allowed:
                raise HttpError(403, "Acesso negado para o seu perfil")
            return func(request, *args, **kwargs)

        wrapper.allowed_roles = allowed  # útil para documentação/testes
        return wrapper

    return decorator


# Atalhos semânticos
WRITE_ROLES = (Role.ADMIN, Role.CONSULTOR, Role.PRODUCAO)
ALL_ROLES = tuple(Role)
