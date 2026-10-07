from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import update_last_login
from ninja import Router
from ninja.errors import HttpError

from apps.accounts.schemas import AccessTokenOut, ErrorOut, LoginIn, RefreshIn, TokenPairOut, UserOut
from apps.accounts.tokens import (
    REFRESH,
    TokenError,
    build_user_claims,
    create_access_token,
    create_refresh_token,
    decode_token,
)

router = Router()


def _user_payload(user) -> dict:
    claims = build_user_claims(user)
    return {
        "id": claims["user_id"],
        "name": claims["name"],
        "email": claims["email"],
        "role": claims["role"],
        "productions": claims["productions"],
    }


@router.post(
    "/token/",
    auth=None,
    response={200: TokenPairOut, 401: ErrorOut},
    summary="Login: troca e-mail/senha por access + refresh token",
)
def obtain_token(request, payload: LoginIn):
    user = authenticate(request, username=payload.email.strip().lower(), password=payload.password)
    if user is None or not user.is_active:
        raise HttpError(401, "Credenciais inválidas")

    update_last_login(None, user)
    access, expires_in = create_access_token(user)
    return {
        "access": access,
        "refresh": create_refresh_token(user),
        "expires_in": expires_in,
        "user": _user_payload(user),
    }


@router.post(
    "/token/refresh/",
    auth=None,
    response={200: AccessTokenOut, 401: ErrorOut},
    summary="Renova o access token a partir do refresh token",
)
def refresh_token(request, payload: RefreshIn):
    try:
        data = decode_token(payload.refresh, REFRESH)
    except TokenError as exc:
        raise HttpError(401, exc.detail) from exc

    user = get_user_model().objects.filter(pk=data["sub"], is_active=True).first()
    if user is None:
        raise HttpError(401, "Usuário inativo ou inexistente")

    # Claims são recalculadas: mudanças de perfil/produções valem já no próximo refresh.
    access, expires_in = create_access_token(user)
    return {"access": access, "expires_in": expires_in}


@router.get("/me/", response={200: UserOut, 401: ErrorOut}, summary="Dados do usuário autenticado")
def me(request):
    return _user_payload(request.auth)
