# Configuração compartilhada pelos scripts de deploy. Ajuste PROJECT_ID antes do primeiro uso.
# Qualquer valor pode ser sobrescrito por variável de ambiente: PROJECT_ID=meu-proj ./deploy/deploy.sh

PROJECT_ID="${PROJECT_ID:-SEU-PROJETO-GCP}"
REGION="${REGION:-southamerica-east1}"            # São Paulo

# Cloud SQL
SQL_INSTANCE="${SQL_INSTANCE:-conectaverde-db}"
SQL_TIER="${SQL_TIER:-db-f1-micro}"               # menor custo; suba para db-custom-1-3840 em produção
DB_NAME="${DB_NAME:-conectaverde}"
DB_USER="${DB_USER:-conectaverde_app}"

# Cloud Run
SERVICE="${SERVICE:-conectaverde-api}"
SERVICE_ACCOUNT_NAME="${SERVICE_ACCOUNT_NAME:-conectaverde-run}"
AR_REPO="${AR_REPO:-conectaverde}"                # Artifact Registry (docker)

# Front-end autorizado (CORS)
CORS_ALLOWED_ORIGINS="${CORS_ALLOWED_ORIGINS:-http://localhost:3000}"
CORS_ALLOWED_ORIGIN_REGEXES="${CORS_ALLOWED_ORIGIN_REGEXES:-^https://conectaverde.*\\.vercel\\.app\$}"

# Derivados (não editar)
INSTANCE_CONNECTION_NAME="${PROJECT_ID}:${REGION}:${SQL_INSTANCE}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
IMAGE_BASE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${SERVICE}"
