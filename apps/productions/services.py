"""Regras de visibilidade de produções por perfil (reutilizadas pela API e pelo JWT)."""
from django.db.models import QuerySet

from apps.core.choices import Role
from apps.productions.models import Production, UserProductionPermission


def visible_productions(user) -> QuerySet[Production]:
    qs = Production.objects.filter(is_active=True)
    if user.role == Role.ADMIN:
        return qs
    return qs.filter(permissions__user=user).distinct()


def productions_claims_for(user) -> list[dict]:
    """Lista compacta de produções para o JWT/`/me`. ADMIN recebe todas as ativas."""
    if user.role == Role.ADMIN:
        return [
            {"id": str(p.id), "name": p.name, "code": p.code, "department": None}
            for p in Production.objects.filter(is_active=True).only("id", "name", "code")
        ]

    perms = (
        UserProductionPermission.objects.filter(user=user, production__is_active=True)
        .select_related("production")
        .order_by("production__name")
    )
    return [
        {
            "id": str(perm.production.id),
            "name": perm.production.name,
            "code": perm.production.code,
            "department": perm.department or None,
        }
        for perm in perms
    ]
