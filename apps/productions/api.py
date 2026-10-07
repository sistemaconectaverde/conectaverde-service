from typing import List
from uuid import UUID

from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Query, Router, Status
from ninja.errors import HttpError

from apps.accounts.schemas import ErrorOut
from apps.accounts.security import roles_allowed
from apps.core.choices import Role
from apps.productions.models import Production
from apps.productions.schemas import ProductionFilters, ProductionIn, ProductionOut
from apps.productions.services import visible_productions

router = Router()


@router.get("/", response=List[ProductionOut], summary="Lista as produções visíveis para o usuário")
def list_productions(request, filters: Query[ProductionFilters]):
    qs = visible_productions(request.auth)
    if filters.status:
        qs = qs.filter(status=filters.status)
    if filters.q:
        qs = qs.filter(Q(name__icontains=filters.q) | Q(client_name__icontains=filters.q))
    return qs.order_by("name")


@router.get("/{production_id}/", response={200: ProductionOut, 404: ErrorOut}, summary="Detalhe de uma produção")
def get_production(request, production_id: UUID):
    # 404 (e não 403) para não revelar a existência de produções de outros clientes.
    return get_object_or_404(visible_productions(request.auth), pk=production_id)


@router.post("/", response={201: ProductionOut, 409: ErrorOut}, summary="Cria produção (somente ADMIN)")
@roles_allowed(Role.ADMIN)
def create_production(request, payload: ProductionIn):
    try:
        production = Production.objects.create(**payload.dict())
    except IntegrityError as exc:
        raise HttpError(409, "Já existe uma produção com este código") from exc
    return Status(201, production)
