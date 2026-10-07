"""
Configurações do Conecta Verde Service.

Tudo que muda entre ambientes vem de variáveis de ambiente (12-factor):
- Local: arquivo .env (copie de .env.example).
- Cloud Run: variáveis do serviço + segredos do Secret Manager.

Banco de dados (em ordem de prioridade):
1. DATABASE_URL  -> ex.: postgres://user:pass@127.0.0.1:5432/conectaverde (Cloud SQL Auth Proxy / Docker)
2. DB_NAME + CLOUD_SQL_CONNECTION_NAME -> socket Unix /cloudsql/<projeto:regiao:instancia> (Cloud Run)
3. DB_NAME + DB_HOST -> conexão TCP comum
4. SQLite local (somente com DJANGO_DEBUG=1, para testes rápidos)
"""
from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega .env em desenvolvimento (no Cloud Run o arquivo não existe e nada acontece).
try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:  # pragma: no cover
    pass


def env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    return value if value not in (None, "") else default


def env_bool(name: str, default: bool = False) -> bool:
    value = env(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "sim"}


def env_list(name: str, default: str = "") -> list[str]:
    raw = env(name, default) or ""
    return [item.strip() for item in raw.split(",") if item.strip()]


# --------------------------------------------------------------------------------------
# Núcleo
# --------------------------------------------------------------------------------------
DEBUG = env_bool("DJANGO_DEBUG", False)

SECRET_KEY = env("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-insecure-change-me"
    else:
        raise ImproperlyConfigured("Defina DJANGO_SECRET_KEY (no Cloud Run, via Secret Manager).")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
# Cloud Run gera hosts *.run.app; permita-os explicitamente via env, ex.: ".run.app"

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # terceiros
    "corsheaders",
    "ninja",
    # domínio Conecta Verde
    "apps.core",
    "apps.accounts",
    "apps.productions",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --------------------------------------------------------------------------------------
# Banco de dados (Cloud SQL / PostgreSQL)
# --------------------------------------------------------------------------------------
def _database_config() -> dict:
    conn_max_age = int(env("DB_CONN_MAX_AGE", "60"))

    database_url = env("DATABASE_URL")
    if database_url:
        import dj_database_url

        return dj_database_url.parse(database_url, conn_max_age=conn_max_age, conn_health_checks=True)

    db_name = env("DB_NAME")
    if db_name:
        instance = env("CLOUD_SQL_CONNECTION_NAME")
        host = f"/cloudsql/{instance}" if instance else env("DB_HOST", "127.0.0.1")
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db_name,
            "USER": env("DB_USER", "postgres"),
            "PASSWORD": env("DB_PASSWORD", ""),
            "HOST": host,
            "PORT": "" if instance else env("DB_PORT", "5432"),
            "CONN_MAX_AGE": conn_max_age,
            "CONN_HEALTH_CHECKS": True,
        }

    if DEBUG:
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}

    raise ImproperlyConfigured(
        "Banco não configurado. Defina DATABASE_URL ou DB_NAME (+ CLOUD_SQL_CONNECTION_NAME no Cloud Run)."
    )


DATABASES = {"default": _database_config()}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------------------
# Autenticação
# --------------------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

JWT = {
    "SIGNING_KEY": env("JWT_SIGNING_KEY", SECRET_KEY),
    "ALGORITHM": "HS256",
    "ISSUER": env("JWT_ISSUER", "conectaverde-service"),
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(env("JWT_ACCESS_TTL_MINUTES", "15"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(env("JWT_REFRESH_TTL_DAYS", "7"))),
}

# --------------------------------------------------------------------------------------
# CORS (Front-end Next.js na Vercel)
# --------------------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
# Previews da Vercel mudam de URL a cada deploy: ex. ^https://conectaverde-.*\.vercel\.app$
CORS_ALLOWED_ORIGIN_REGEXES = env_list("CORS_ALLOWED_ORIGIN_REGEXES")
CORS_ALLOW_CREDENTIALS = True

# --------------------------------------------------------------------------------------
# Internacionalização
# --------------------------------------------------------------------------------------
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------------------
# Arquivos estáticos (admin + Swagger servidos pelo WhiteNoise no Cloud Run)
# --------------------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

# --------------------------------------------------------------------------------------
# Segurança atrás do proxy HTTPS do Cloud Run
# --------------------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

# --------------------------------------------------------------------------------------
# Logs no stdout (capturados pelo Cloud Logging)
# --------------------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "%(levelname)s %(name)s %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
}
