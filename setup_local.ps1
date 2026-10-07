# setup_local.ps1 - prepara o ambiente de desenvolvimento no Windows (rodar uma vez).
#
# Como usar (PowerShell, dentro da pasta do projeto):
#   powershell -ExecutionPolicy Bypass -File .\setup_local.ps1
#
# O que ele faz:
#   1. Cria o ambiente virtual Python na pasta .venv (se ainda não existir)
#   2. Instala as bibliotecas do requirements-dev.txt
#   3. Cria o arquivo .env a partir do .env.example (se ainda não existir)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "== Conecta Verde: preparando ambiente local ==" -ForegroundColor Green

# Confere se o Python existe
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python não encontrado. Instale em https://www.python.org/downloads/ (marque 'Add Python to PATH')." -ForegroundColor Red
    exit 1
}
Write-Host ("Python encontrado: " + (python --version 2>&1))

# 1. Ambiente virtual
if (Test-Path ".venv\Scripts\python.exe") {
    Write-Host "[1/3] Ambiente virtual .venv já existe (mantido)."
} else {
    Write-Host "[1/3] Criando ambiente virtual em .venv ..."
    python -m venv .venv
}

# 2. Bibliotecas
Write-Host "[2/3] Instalando bibliotecas (pode levar alguns minutos) ..."
& .\.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro ao instalar as bibliotecas. Copie a mensagem acima e mande para o Claude." -ForegroundColor Red
    exit 1
}

# 3. Arquivo .env
if (Test-Path ".env") {
    Write-Host "[3/3] Arquivo .env já existe (mantido)."
} else {
    Copy-Item ".env.example" ".env"
    Write-Host "[3/3] Arquivo .env criado a partir do .env.example."
}

Write-Host ""
Write-Host "Pronto!" -ForegroundColor Green
Write-Host "Para ativar o ambiente neste terminal:  .\.venv\Scripts\Activate.ps1"
Write-Host "Para rodar os testes (com o banco ligado: docker compose up -d db):  pytest"
Write-Host ""
