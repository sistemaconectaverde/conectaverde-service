#!/usr/bin/env bash
# Provisionamento ÚNICO do GCP (TSK-BE-01): APIs, Cloud SQL PostgreSQL 16, segredos,
# Artifact Registry e conta de serviço do Cloud Run.
# Rode no Cloud Shell ou no Git Bash com o gcloud autenticado:  bash deploy/setup_gcp.sh
set -euo pipefail
cd "$(dirname "$0")/.."
source deploy/config.sh

if [[ "$PROJECT_ID" == "SEU-PROJETO-GCP" ]]; then
  echo "Defina PROJECT_ID em deploy/config.sh (ou: PROJECT_ID=xxx bash deploy/setup_gcp.sh)"; exit 1
fi

gcloud config set project "$PROJECT_ID"

echo ">> Habilitando APIs"
gcloud services enable \
  run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com \
  artifactregistry.googleapis.com cloudbuild.googleapis.com iam.googleapis.com

echo ">> Artifact Registry"
gcloud artifacts repositories describe "$AR_REPO" --location "$REGION" >/dev/null 2>&1 || \
  gcloud artifacts repositories create "$AR_REPO" --repository-format=docker --location "$REGION" \
    --description "Imagens do Conecta Verde"

echo ">> Cloud SQL (PostgreSQL 16) — pode levar ~10 min na primeira vez"
gcloud sql instances describe "$SQL_INSTANCE" >/dev/null 2>&1 || \
  gcloud sql instances create "$SQL_INSTANCE" \
    --database-version=POSTGRES_16 --edition=ENTERPRISE --tier="$SQL_TIER" \
    --region="$REGION" --storage-size=10 --storage-auto-increase \
    --backup-start-time=05:00

gcloud sql databases describe "$DB_NAME" --instance "$SQL_INSTANCE" >/dev/null 2>&1 || \
  gcloud sql databases create "$DB_NAME" --instance "$SQL_INSTANCE"

create_secret() {  # nome valor
  if gcloud secrets describe "$1" >/dev/null 2>&1; then
    echo "   segredo $1 já existe (mantido)"
  else
    printf '%s' "$2" | gcloud secrets create "$1" --data-file=- --replication-policy=automatic
  fi
}
rand() { python3 -c "import secrets; print(secrets.token_urlsafe(48))"; }

echo ">> Segredos (Secret Manager)"
DB_PASSWORD_VALUE="$(rand)"
create_secret django-secret-key "$(rand)"
create_secret jwt-signing-key "$(rand)"
if ! gcloud secrets describe db-password >/dev/null 2>&1; then
  create_secret db-password "$DB_PASSWORD_VALUE"
  gcloud sql users create "$DB_USER" --instance "$SQL_INSTANCE" --password "$DB_PASSWORD_VALUE"
fi
create_secret demo-users-password "Demo-$(python3 -c 'import secrets; print(secrets.token_hex(4))')!"

echo ">> Conta de serviço do Cloud Run"
gcloud iam service-accounts describe "$SERVICE_ACCOUNT" >/dev/null 2>&1 || \
  gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" --display-name "Conecta Verde Cloud Run"
for role in roles/cloudsql.client roles/secretmanager.secretAccessor; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member "serviceAccount:${SERVICE_ACCOUNT}" --role "$role" --condition=None >/dev/null
done

echo
echo "Pronto! Conexão do Cloud SQL: ${INSTANCE_CONNECTION_NAME}"
echo "Senha dos usuários demo:  gcloud secrets versions access latest --secret demo-users-password"
echo "Próximo passo:            bash deploy/deploy.sh"
