"""Settings para pytest. Usa o banco do .env (PostgreSQL) se houver; senão SQLite."""
import os

os.environ.setdefault("DJANGO_DEBUG", "1")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key")

from config.settings import *  # noqa: E402,F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # testes rápidos
JWT = {**JWT, "SIGNING_KEY": "test-jwt-signing-key-with-at-least-32-bytes!"}  # noqa: F405

# WhiteNoise não é necessário nos testes (evita aviso "No directory at: staticfiles").
MIDDLEWARE = [m for m in MIDDLEWARE if "whitenoise" not in m]  # noqa: F405
