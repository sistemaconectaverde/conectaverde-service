"""Instância central do Django Ninja. Swagger: /api/docs | OpenAPI: /api/openapi.json"""
from ninja import NinjaAPI

from apps.accounts.api import router as auth_router
from apps.accounts.security import JWTAuth
from apps.core.api import admin_router, health_router
from apps.productions.api import router as productions_router

api = NinjaAPI(
    title="Conecta Verde API",
    version="0.1.0",
    description=(
        "API da Plataforma Digital de Gestão de Sustentabilidade Conecta Verde (MVP 1).\n\n"
        "Autentique em `POST /api/auth/token/` e use o botão **Authorize** com o `access` token."
    ),
    auth=JWTAuth(),  # tudo exige JWT por padrão; rotas públicas usam auth=None
    urls_namespace="api",
)

api.add_router("/health", health_router, tags=["Infra"])
api.add_router("/auth", auth_router, tags=["Autenticação"])
api.add_router("/productions", productions_router, tags=["Produções"])
api.add_router("/admin", admin_router, tags=["Administração"])
