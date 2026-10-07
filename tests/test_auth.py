"""Cobre o roteiro de Teste Integrado da Sprint 1 (CT-01 a CT-07) do lado da API."""
from datetime import timedelta

import jwt
import pytest
from django.conf import settings

from apps.core.choices import Role
from tests.conftest import PASSWORD

pytestmark = pytest.mark.django_db


def _decode(token):
    return jwt.decode(token, settings.JWT["SIGNING_KEY"], algorithms=["HS256"], issuer=settings.JWT["ISSUER"])


# CT-01 -------------------------------------------------------------------------------
@pytest.mark.parametrize("email,password", [("admin@conectaverde.com.br", "errada"), ("ninguem@x.com", PASSWORD)])
def test_ct01_invalid_credentials_return_401(api_client, admin_user, email, password):
    response = api_client.post(
        "/api/auth/token/", data={"email": email, "password": password}, content_type="application/json"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Credenciais inválidas"}


def test_inactive_user_cannot_login(api_client, admin_user):
    admin_user.is_active = False
    admin_user.save()
    response = api_client.post(
        "/api/auth/token/",
        data={"email": admin_user.email, "password": PASSWORD},
        content_type="application/json",
    )
    assert response.status_code == 401


def test_login_is_case_insensitive_on_email(login, admin_user):
    data = login("ADMIN@ConectaVerde.com.br")
    assert data["user"]["email"] == "admin@conectaverde.com.br"


# CT-02 a CT-05 -----------------------------------------------------------------------
def test_ct02_admin_token_has_role_and_all_productions(login, admin_user, production, other_production):
    data = login(admin_user.email)
    claims = _decode(data["access"])
    assert claims["role"] == Role.ADMIN
    assert claims["user_id"] == str(admin_user.id)
    assert claims["name"] == admin_user.name
    assert {p["code"] for p in claims["productions"]} == {"piloto-demo", "outra-producao"}
    assert data["token_type"] == "Bearer"
    assert data["expires_in"] == 15 * 60


def test_ct03_consultor_token_has_only_linked_productions(login, consultor_user, other_production):
    claims = _decode(login(consultor_user.email)["access"])
    assert claims["role"] == Role.CONSULTOR
    assert [p["code"] for p in claims["productions"]] == ["piloto-demo"]


def test_ct04_producao_token_carries_department(login, producao_user):
    claims = _decode(login(producao_user.email)["access"])
    assert claims["role"] == Role.PRODUCAO
    assert claims["productions"][0]["department"] == "EQUIPE"


def test_ct05_readonly_token(login, readonly_user):
    claims = _decode(login(readonly_user.email)["access"])
    assert claims["role"] == Role.READONLY
    assert len(claims["productions"]) == 1


def test_me_returns_authenticated_user(login, auth_get, producao_user):
    token = login(producao_user.email)["access"]
    response = auth_get("/api/auth/me/", token)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == producao_user.email
    assert body["role"] == "PRODUCAO"
    assert body["productions"][0]["code"] == "piloto-demo"


def test_me_without_token_returns_401(api_client):
    assert api_client.get("/api/auth/me/").status_code == 401


# CT-06 -------------------------------------------------------------------------------
@pytest.mark.parametrize("fixture_name", ["producao_user", "consultor_user", "readonly_user"])
def test_ct06_non_admin_gets_403_on_admin_route(request, login, auth_get, fixture_name):
    user = request.getfixturevalue(fixture_name)
    token = login(user.email)["access"]
    response = auth_get("/api/admin/fatores-ghg/", token)
    assert response.status_code == 403
    assert response.json()["detail"] == "Acesso negado para o seu perfil"


def test_ct06_admin_can_access_admin_route(login, auth_get, admin_user):
    token = login(admin_user.email)["access"]
    assert auth_get("/api/admin/fatores-ghg/", token).status_code == 200


# CT-07 -------------------------------------------------------------------------------
def test_ct07_refresh_returns_new_access_token(api_client, login, auth_get, consultor_user):
    tokens = login(consultor_user.email)
    response = api_client.post(
        "/api/auth/token/refresh/", data={"refresh": tokens["refresh"]}, content_type="application/json"
    )
    assert response.status_code == 200
    new_access = response.json()["access"]
    assert _decode(new_access)["role"] == Role.CONSULTOR
    assert auth_get("/api/auth/me/", new_access).status_code == 200


def test_expired_access_token_returns_401(login, auth_get, admin_user):
    jwt_settings = {**settings.JWT, "ACCESS_TOKEN_LIFETIME": timedelta(seconds=-1)}
    from django.test import override_settings

    with override_settings(JWT=jwt_settings):
        token = login(admin_user.email)["access"]
    response = auth_get("/api/auth/me/", token)
    assert response.status_code == 401
    assert response.json()["detail"] == "Token expirado"


def test_access_token_cannot_be_used_as_refresh(api_client, login, admin_user):
    tokens = login(admin_user.email)
    response = api_client.post(
        "/api/auth/token/refresh/", data={"refresh": tokens["access"]}, content_type="application/json"
    )
    assert response.status_code == 401


def test_refresh_token_cannot_be_used_as_access(login, auth_get, admin_user):
    tokens = login(admin_user.email)
    assert auth_get("/api/auth/me/", tokens["refresh"]).status_code == 401


def test_refresh_fails_for_deactivated_user(api_client, login, consultor_user):
    tokens = login(consultor_user.email)
    consultor_user.is_active = False
    consultor_user.save()
    response = api_client.post(
        "/api/auth/token/refresh/", data={"refresh": tokens["refresh"]}, content_type="application/json"
    )
    assert response.status_code == 401


def test_tampered_token_is_rejected(login, auth_get, admin_user):
    token = login(admin_user.email)["access"]
    assert auth_get("/api/auth/me/", token[:-2] + "xx").status_code == 401
