"""
Seed neutro da Sprint 1: 1 produção demo + 4 usuários (um por perfil).

    python manage.py seed_demo                       # usa DEMO_USERS_PASSWORD
    python manage.py seed_demo --password "S3nh@Forte"

Idempotente: pode rodar várias vezes (atualiza em vez de duplicar).
"""
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.choices import Department, Role
from apps.productions.models import Production, UserProductionPermission

DEMO_PRODUCTION = {
    "code": "producao-piloto-serie-demo",
    "name": "Produção Piloto — Série Demo",
    "client_name": "Produtora Demo",
    "location": "Estúdio Demo",
    "city": "Rio de Janeiro",
    "state": "RJ",
    "episodes_count": 10,
    "shooting_days": 30,
    "pre_production_days": 15,
    "post_production_days": 20,
    "status": Production.Status.EM_ANDAMENTO,
}

DEMO_USERS = [
    # email, nome, perfil, departamento (vínculo), is_staff
    ("admin@conectaverde.com.br", "Admin Conecta Verde", Role.ADMIN, None, True),
    ("consultor@conectaverde.com.br", "Consultor Demo", Role.CONSULTOR, "", False),
    ("operacao@produtora-demo.com.br", "Operação Set Demo", Role.PRODUCAO, Department.EQUIPE, False),
    ("executivo@cliente-demo.com.br", "Executivo Cliente Demo", Role.READONLY, "", False),
]


class Command(BaseCommand):
    help = "Cria/atualiza a produção demo e os 4 usuários de teste (ADMIN, CONSULTOR, PRODUCAO, READONLY)."

    def add_arguments(self, parser):
        parser.add_argument("--password", help="Senha dos 4 usuários (padrão: env DEMO_USERS_PASSWORD).")

    @transaction.atomic
    def handle(self, *args, **options):
        password = options.get("password") or os.environ.get("DEMO_USERS_PASSWORD")
        if not password:
            if settings.DEBUG:
                password = "ConectaVerde@2026"
            else:
                raise CommandError("Informe --password ou defina DEMO_USERS_PASSWORD.")

        code = DEMO_PRODUCTION["code"]
        defaults = {k: v for k, v in DEMO_PRODUCTION.items() if k != "code"}
        production, _ = Production.objects.update_or_create(code=code, defaults=defaults)
        self.stdout.write(f"Produção: {production.name}")

        User = get_user_model()
        admin_user = None
        for email, name, role, department, is_staff in DEMO_USERS:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"name": name, "role": role, "is_staff": is_staff, "is_superuser": is_staff},
            )
            user.name, user.role, user.is_active = name, role, True
            user.is_staff = user.is_superuser = is_staff
            user.set_password(password)
            user.save()

            if role == Role.ADMIN:
                admin_user = user
            elif department is not None:
                UserProductionPermission.objects.update_or_create(
                    user=user,
                    production=production,
                    defaults={"department": department, "granted_by": admin_user},
                )

            status = "criado" if created else "atualizado"
            self.stdout.write(f"  [{role}] {email} ({status})")

        self.stdout.write(self.style.SUCCESS("Seed concluído."))
