import pytest
from django.test import Client

from apps.accounts.models import User
from apps.core.choices import Department, Role
from apps.productions.models import Production, UserProductionPermission

PASSWORD = "Senha@Teste123"


@pytest.fixture
def api_client():
    return Client()


@pytest.fixture
def production(db):
    return Production.objects.create(name="Produção Piloto — Série Demo", code="piloto-demo")


@pytest.fixture
def other_production(db):
    return Production.objects.create(name="Outra Produção", code="outra-producao")


def _make_user(email, role, production=None, department=""):
    user = User.objects.create_user(email=email, password=PASSWORD, name=email.split("@")[0], role=role)
    if production is not None:
        UserProductionPermission.objects.create(user=user, production=production, department=department)
    return user


@pytest.fixture
def admin_user(db):
    return _make_user("admin@conectaverde.com.br", Role.ADMIN)


@pytest.fixture
def consultor_user(production):
    return _make_user("consultor@conectaverde.com.br", Role.CONSULTOR, production)


@pytest.fixture
def producao_user(production):
    return _make_user("operacao@produtora-demo.com.br", Role.PRODUCAO, production, Department.EQUIPE)


@pytest.fixture
def readonly_user(production):
    return _make_user("executivo@cliente-demo.com.br", Role.READONLY, production)


@pytest.fixture
def login(api_client):
    """Faz login e devolve o JSON da resposta (access, refresh, user...)."""

    def _login(email, password=PASSWORD):
        response = api_client.post(
            "/api/auth/token/",
            data={"email": email, "password": password},
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        return response.json()

    return _login


@pytest.fixture
def auth_get(api_client):
    def _get(url, token):
        return api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {token}")

    return _get
