#!/usr/bin/env bash
# Build + migrations + deploy no Cloud Run (TSK-BE-06).
#   bash deploy/deploy.sh            -> build, migrate, deploy
#   bash deploy/deploy.sh --seed     -> idem + roda o seed dos 4 usuários demo
set -euo pipefail
cd "$(dirname "$0")/.."
source deploy/config.sh

RUN_SEED=false
[[ "${1:-}" == "--seed" ]] && RUN_SEED=true

TAG="$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)"
IMAGE="${IMAGE_BASE}:${TAG}"

gcloud config set project "$PROJECT_ID" >/dev/null

echo ">> Build da imagem no Cloud Build: $IMAGE"
gcloud builds submit --tag "$IMAGE" .

# Variáveis comuns (arquivo YAML evita problemas com vírgulas/regex na linha de comando)
ENV_FILE="$(mktemp)"
trap 'rm -f "$ENV_FILE"' EXIT
cat > "$ENV_FILE" <<EOF
DJANGO_DEBUG: "0"
DJANGO_ALLOWED_HOSTS: ".run.app"
DJANGO_CSRF_TRUSTED_ORIGINS: "https://*.run.app"
DB_NAME: "${DB_NAME}"
DB_USER: "${DB_USER}"
CLOUD_SQL_CONNECTION_NAME: "${INSTANCE_CONNECTION_NAME}"
CORS_ALLOWED_ORIGINS: "${CORS_ALLOWED_ORIGINS}"
CORS_ALLOWED_ORIGIN_REGEXES: '${CORS_ALLOWED_ORIGIN_REGEXES}'
EOF
SECRETS="DJANGO_SECRET_KEY=django-secret-key:latest,JWT_SIGNING_KEY=jwt-signing-key:latest,DB_PASSWORD=db-password:latest"

run_job() {  # nome  args-do-manage.py  [segredos extras]
  local name="$1" args="$2" extra="${3:-}"
  gcloud run jobs deploy "$name" \
    --image "$IMAGE" --region "$REGION" \
    --service-account "$SERVICE_ACCOUNT" \
    --set-cloudsql-instances "$INSTANCE_CONNECTION_NAME" \
    --env-vars-file "$ENV_FILE" \
    --set-secrets "${SECRETS}${extra}" \
    --command python --args "$args" \
    --max-retries 0 --task-timeout 10m
  gcloud run jobs execute "$name" --region "$REGION" --wait
}

echo ">> Migrations no Cloud SQL"
run_job "${SERVICE}-migrate" "manage.py,migrate,--noinput"

if $RUN_SEED; then
  echo ">> Seed dos usuários demo"
  run_job "${SERVICE}-seed" "manage.py,seed_demo" ",DEMO_USERS_PASSWORD=demo-users-password:latest"
fi

echo ">> Deploy do serviço Cloud Run"
gcloud run deploy "$SERVICE" \
  --image "$IMAGE" --region "$REGION" \
  --service-account "$SERVICE_ACCOUNT" \
  --set-cloudsql-instances "$INSTANCE_CONNECTION_NAME" \
  --env-vars-file "$ENV_FILE" \
  --set-secrets "$SECRETS" \
  --allow-unauthenticated \
  --port 8080 --memory 512Mi --cpu 1 \
  --min-instances 0 --max-instances 3 --concurrency 40

URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --format 'value(status.url)')"
echo
echo "API no ar:  ${URL}/api/docs"
echo "Health:     ${URL}/api/health/"
