# Cloud SQL Auth Proxy (desenvolvimento local contra o banco da nuvem)

O proxy cria um túnel autenticado (IAM) entre a sua máquina e o Cloud SQL, sem abrir IP público
no banco e sem guardar certificados. Credenciais ficam só no `.env` (que não vai para o git).

## Windows (PowerShell)

```powershell
# 1. Login (uma vez)
gcloud auth login
gcloud auth application-default login

# 2. Baixar o proxy (uma vez) para a pasta do projeto — já está no .gitignore
Invoke-WebRequest -Uri https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.14.1/cloud-sql-proxy.x64.exe -OutFile cloud-sql-proxy.exe

# 3. Subir o túnel (deixe este terminal aberto)
.\cloud-sql-proxy.exe --port 5432 SEU-PROJETO-GCP:southamerica-east1:conectaverde-db
```

## Linux / macOS / Cloud Shell

```bash
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.14.1/cloud-sql-proxy.linux.amd64
chmod +x cloud-sql-proxy
./cloud-sql-proxy --port 5432 SEU-PROJETO-GCP:southamerica-east1:conectaverde-db
```

## Apontar o Django para o proxy

No `.env`:

```
DATABASE_URL=postgres://conectaverde_app:SENHA@127.0.0.1:5432/conectaverde
```

A senha está no Secret Manager:

```
gcloud secrets versions access latest --secret db-password
```

Depois é só `python manage.py migrate`, `python manage.py seed_demo` etc. — direto no Cloud SQL.

> Verifique a versão mais recente do proxy em https://github.com/GoogleCloudPlatform/cloud-sql-proxy/releases
