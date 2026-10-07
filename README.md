# conectaverde-service

API back-end da **Plataforma Digital Conecta Verde** (gestão de sustentabilidade / inventário GEE para produções audiovisuais).

**Stack:** Python 3.12 · Django 5.2 · Django Ninja (OpenAPI/Swagger) · PostgreSQL 16 no **Google Cloud SQL** · **Google Cloud Run** · JWT (PyJWT)

Swagger: **`/api/docs`** · OpenAPI JSON: `/api/openapi.json` · Django Admin: `/django-admin/`

---

## Entregáveis da Sprint 1 (28/09 – 09/10/2026)

| Tarefa | O que está pronto |
|---|---|
| TSK-BE-01 | `deploy/setup_gcp.sh` provisiona Cloud SQL PostgreSQL 16, Secret Manager, Artifact Registry e conta de serviço; `deploy/cloud_sql_proxy.md` |
| TSK-BE-02 | Projeto Django + Django Ninja, configuração 100% por variáveis de ambiente (`.env`), Swagger em `/api/docs` |
| TSK-BE-03 | Models `User` (login por e-mail, 4 perfis), `Production`, `UserProductionPermission` + migrations |
| TSK-BE-04 | `POST /api/auth/token/`, `POST /api/auth/token/refresh/`, `GET /api/auth/me/` — JWT com `user_id`, `name`, `role` e `productions` |
| TSK-BE-05 | Decorator `@roles_allowed(...)` e `GET /api/productions/` filtrado por perfil |
| TSK-BE-06 | `Dockerfile` multi-stage, `deploy/deploy.sh` (Cloud Build → migrations via Cloud Run Job → Cloud Run) e `seed_demo` com os 4 usuários |

Os testes automatizados em `tests/` cobrem o lado da API do roteiro **CT-01 a CT-07**.

## Estrutura

```
config/              settings (env), urls, instância NinjaAPI (config/api.py)
apps/core/           enums de domínio (Role, DataStatus, Department), modelo abstrato AuditedRecord, health, rotas admin
apps/accounts/       User, JWT (tokens.py), JWTAuth + @roles_allowed (security.py), endpoints de auth, seed_demo
apps/productions/    Production, UserProductionPermission, regras de visibilidade, endpoints
deploy/              scripts gcloud (setup único + deploy) e guia do Cloud SQL Auth Proxy
tests/               pytest (auth/RBAC/produções/seed)
```

## Perfis (RBAC)

| Perfil | Vê produções | Observações |
|---|---|---|
| `ADMIN` | todas | acesso global, rotas `/api/admin/*`, cria produções |
| `CONSULTOR` | vinculadas | produções sob sua responsabilidade |
| `PRODUCAO` | vinculadas | vínculo carrega o **departamento** (EQUIPE, CATERING, RESIDUOS…) |
| `READONLY` | vinculadas | somente leitura |

Proteger um endpoint:

```python
from apps.accounts.security import roles_allowed
from apps.core.choices import Role

@router.post("/lancamentos/")
@roles_allowed(Role.ADMIN, Role.CONSULTOR, Role.PRODUCAO)   # sempre ABAIXO do decorator do router
def criar_lancamento(request, payload: LancamentoIn):
    user = request.auth
```

Erros seguem o formato `{"detail": "..."}`: **401** credenciais/token inválido ou expirado (`"Token expirado"` → o front chama o refresh), **403** perfil sem permissão.

### Contrato de autenticação (para o Next.js)

```http
POST /api/auth/token/            {"email": "...", "password": "..."}
→ 200 {"access", "refresh", "token_type": "Bearer", "expires_in": 900, "user": {id, name, email, role, productions[]}}
→ 401 {"detail": "Credenciais inválidas"}

POST /api/auth/token/refresh/    {"refresh": "..."}
→ 200 {"access", "token_type", "expires_in"}

GET  /api/auth/me/               Authorization: Bearer <access>
```

Claims do access token: `user_id`, `name`, `email`, `role`, `productions: [{id, name, code, department}]`, `exp` (15 min). Refresh: 7 dias.

---

## Rodando localmente (Windows / PowerShell)

Pré-requisitos: Python 3.12+, e Docker Desktop **ou** o Cloud SQL Auth Proxy.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env

# Banco: PostgreSQL local em Docker (porta 5433)...
docker compose up -d db
# ...ou o Cloud SQL via proxy: veja deploy/cloud_sql_proxy.md e ajuste DATABASE_URL no .env

python manage.py migrate
python manage.py seed_demo          # 4 usuários demo, senha = DEMO_USERS_PASSWORD do .env
python manage.py runserver 8000     # http://localhost:8000/api/docs
```

Testes e conferência das migrations:

```powershell
pytest
python manage.py makemigrations --check --dry-run   # deve dizer "No changes detected"
```

Tudo em Docker (API + banco): `docker compose up --build` → http://localhost:8080/api/docs

### Usuários demo (`seed_demo`)

| Perfil | E-mail |
|---|---|
| ADMIN | admin@conectaverde.com.br |
| CONSULTOR | consultor@conectaverde.com.br |
| PRODUCAO | operacao@produtora-demo.com.br (departamento EQUIPE) |
| READONLY | executivo@cliente-demo.com.br |

Todos vinculados à produção **"Produção Piloto — Série Demo"**.

---

## Deploy no Google Cloud (Cloud SQL + Cloud Run)

Use o **Cloud Shell** (já tem gcloud) ou Git Bash com o [gcloud CLI](https://cloud.google.com/sdk/docs/install) autenticado.

1. Edite `deploy/config.sh` → `PROJECT_ID` (e, se quiser, região/nomes/CORS).
2. Provisionamento único (~10 min na primeira vez):
   ```bash
   bash deploy/setup_gcp.sh
   ```
   Cria: instância `conectaverde-db` (PostgreSQL 16, `db-f1-micro`, São Paulo), banco e usuário, segredos
   `django-secret-key`, `jwt-signing-key`, `db-password`, `demo-users-password`, repositório no Artifact Registry e
   a conta de serviço `conectaverde-run` com `cloudsql.client` + `secretmanager.secretAccessor`.
3. Deploy (primeira vez com seed):
   ```bash
   bash deploy/deploy.sh --seed
   ```
   O script faz o build no Cloud Build, roda `migrate` como **Cloud Run Job** conectado ao Cloud SQL e publica o
   serviço `conectaverde-api`. Ao final mostra a URL do Swagger. Nos próximos deploys: `bash deploy/deploy.sh`.

Como o Cloud Run conecta no Cloud SQL: o serviço recebe `--set-cloudsql-instances`, que monta o socket em
`/cloudsql/PROJETO:REGIAO:INSTANCIA`; o settings usa esse caminho quando `CLOUD_SQL_CONNECTION_NAME` está definido.
Segredos nunca ficam na imagem — entram como variáveis via Secret Manager.

### Variáveis de ambiente

| Variável | Uso |
|---|---|
| `DJANGO_SECRET_KEY` | obrigatória fora do modo debug |
| `DJANGO_DEBUG` | `1` só em desenvolvimento |
| `DJANGO_ALLOWED_HOSTS` | ex.: `.run.app` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | ex.: `https://*.run.app` (login no django-admin) |
| `DATABASE_URL` | conexão completa (local/proxy) |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `CLOUD_SQL_CONNECTION_NAME` | conexão via socket no Cloud Run |
| `JWT_SIGNING_KEY`, `JWT_ACCESS_TTL_MINUTES`, `JWT_REFRESH_TTL_DAYS` | tokens |
| `CORS_ALLOWED_ORIGINS`, `CORS_ALLOWED_ORIGIN_REGEXES` | front-end (localhost e previews da Vercel) |
| `DEMO_USERS_PASSWORD` | senha do `seed_demo` |

---

## Próximas sprints

`apps/core/models.py` já traz o modelo abstrato **`AuditedRecord`** (status CONFIRMADO / DECLARADO / ESTIMADO /
NAO_INFORMADO, usuário e departamento de origem, metodologia, versão do fator de emissão, anexo NF/MTR). Os módulos de
lançamento (transporte, geradores, energia, resíduos…) devem herdar dele para manter a trilha de auditoria.
