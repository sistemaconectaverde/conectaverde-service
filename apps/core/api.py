from django.db import connection
from ninja import Router

from apps.accounts.security import roles_allowed
from apps.core.choices import Role

# ---------------------------------------------------------------------------
# Health check (usado pelo Cloud Run e pelo time de front)
# ---------------------------------------------------------------------------
health_router = Router()


@health_router.get("/", auth=None, summary="Health check (API + banco)")
def health(request):
    db_ok = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:  # noqa: BLE001
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "database": db_ok}


# ---------------------------------------------------------------------------
# Área administrativa (somente ADMIN). Os fatores GHG chegam na Sprint 5;
# a rota já existe para validar o bloqueio por perfil (CT-06).
# ---------------------------------------------------------------------------
admin_router = Router()


@admin_router.get("/fatores-ghg/", summary="Fatores de emissão GHG (somente ADMIN)")
@roles_allowed(Role.ADMIN)
def list_emission_factors(request):
    return {"items": [], "detail": "Catálogo de fatores será implementado na Sprint 5."}
