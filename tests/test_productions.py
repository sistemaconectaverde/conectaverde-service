import pytest
from django.core.management import call_command

from apps.accounts.models import User
from apps.core.choices import Role
from apps.productions.models import Production, UserProductionPermission

pytestmark = pytest.mark.django_db


def test_admin_lists_all_productions(login, auth_get, admin_user, production, other_production):
    token = login(admin_user.email)["access"]
    response = auth_get("/api/productions/", token)
    assert response.status_code == 200
    assert {p["code"] for p in response.json()} == {"piloto-demo", "outra-producao"}


@pytest.mark.parametrize("fixture_name", ["consultor_user", "producao_user", "readonly_user"])
def test_linked_users_list_only_their_productions(request, login, auth_get, other_production, fixture_name):
    user = request.getfixturevalue(fixture_name)
    token = login(user.email)["access"]
    response = auth_get("/api/productions/", token)
    assert response.status_code == 200
    assert [p["code"] for p in response.json()] == ["piloto-demo"]


def test_inactive_productions_are_hidden(login, auth_get, admin_user, production):
    production.is_active = False
    production.save()
    token = login(admin_user.email)["access"]
    assert auth_get("/api/productions/", token).json() == []


def test_productions_requires_auth(api_client):
    assert api_client.get("/api/productions/").status_code == 401


def test_filter_by_text(login, auth_get, admin_user, production, other_production):
    token = login(admin_user.email)["access"]
    response = auth_get("/api/productions/?q=outra", token)
    assert [p["code"] for p in response.json()] == ["outra-producao"]


def test_detail_of_unlinked_production_returns_404(login, auth_get, consultor_user, other_production):
    token = login(consultor_user.email)["access"]
    assert auth_get(f"/api/productions/{other_production.id}/", token).status_code == 404


def test_detail_of_linked_production(login, auth_get, consultor_user, production):
    token = login(consultor_user.email)["access"]
    response = auth_get(f"/api/productions/{production.id}/", token)
    assert response.status_code == 200
    assert response.json()["name"] == production.name


def test_only_admin_creates_production(api_client, login, admin_user, consultor_user):
    payload = {"name": "Nova Série", "code": "nova-serie", "city": "São Paulo", "state": "SP"}

    token = login(consultor_user.email)["access"]
    response = api_client.post(
        "/api/productions/", data=payload, content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {token}"
    )
    assert response.status_code == 403

    token = login(admin_user.email)["access"]
    response = api_client.post(
        "/api/productions/", data=payload, content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {token}"
    )
    assert response.status_code == 201
    assert response.json()["code"] == "nova-serie"

    response = api_client.post(
        "/api/productions/", data=payload, content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {token}"
    )
    assert response.status_code == 409


def test_seed_demo_is_idempotent(db):
    call_command("seed_demo", password="Seed@2026!")
    call_command("seed_demo", password="Seed@2026!")

    assert Production.objects.count() == 1
    assert User.objects.count() == 4
    assert set(User.objects.values_list("role", flat=True)) == {r.value for r in Role}
    assert UserProductionPermission.objects.count() == 3
    admin = User.objects.get(email="admin@conectaverde.com.br")
    assert admin.check_password("Seed@2026!") and admin.is_superuser


def test_health(api_client, db):
    response = api_client.get("/api/health/")
    assert response.status_code == 200
    assert response.json()["database"] is True


def test_swagger_docs_available(api_client):
    assert api_client.get("/api/docs").status_code == 200
    assert api_client.get("/api/openapi.json").status_code == 200
