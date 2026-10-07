import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Production",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200, verbose_name="nome do projeto")),
                ("code", models.SlugField(max_length=60, unique=True, verbose_name="código")),
                ("client_name", models.CharField(blank=True, max_length=200, verbose_name="produtora / cliente")),
                ("location", models.CharField(blank=True, max_length=200, verbose_name="local")),
                ("city", models.CharField(blank=True, max_length=120, verbose_name="cidade")),
                ("state", models.CharField(blank=True, max_length=2, verbose_name="UF")),
                ("episodes_count", models.PositiveIntegerField(blank=True, null=True, verbose_name="número de episódios")),
                ("shooting_days", models.PositiveIntegerField(blank=True, null=True, verbose_name="dias de filmagem")),
                (
                    "pre_production_days",
                    models.PositiveIntegerField(blank=True, null=True, verbose_name="dias de pré-produção"),
                ),
                (
                    "post_production_days",
                    models.PositiveIntegerField(blank=True, null=True, verbose_name="dias de pós-produção"),
                ),
                ("start_date", models.DateField(blank=True, null=True, verbose_name="início")),
                ("end_date", models.DateField(blank=True, null=True, verbose_name="término")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PLANEJADA", "Planejada"),
                            ("EM_ANDAMENTO", "Em andamento"),
                            ("EM_AUDITORIA", "Em auditoria"),
                            ("CONCLUIDA", "Concluída"),
                        ],
                        default="PLANEJADA",
                        max_length=20,
                        verbose_name="status",
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="ativa")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
            ],
            options={
                "verbose_name": "produção",
                "verbose_name_plural": "produções",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="UserProductionPermission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "department",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("EQUIPE", "Equipe"),
                            ("ELENCO", "Elenco"),
                            ("CONVIDADO", "Convidado"),
                            ("PLATEIA", "Plateia"),
                            ("FIGURINO", "Figurino"),
                            ("MAQUIAGEM", "Maquiagem"),
                            ("ARTE", "Arte"),
                            ("CENARIO", "Cenário"),
                            ("CATERING", "Catering"),
                            ("RESIDUOS", "Resíduos"),
                            ("EQUIPAMENTOS", "Equipamentos"),
                            ("OUTROS", "Outros"),
                        ],
                        help_text="Obrigatório na prática para o perfil PRODUCAO (restringe o lançamento ao departamento).",
                        max_length=20,
                        verbose_name="departamento",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                (
                    "granted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="concedido por",
                    ),
                ),
                (
                    "production",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="permissions",
                        to="productions.production",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="production_permissions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "permissão em produção",
                "verbose_name_plural": "permissões em produções",
            },
        ),
        migrations.AddField(
            model_name="production",
            name="members",
            field=models.ManyToManyField(
                blank=True,
                related_name="productions",
                through="productions.UserProductionPermission",
                through_fields=("production", "user"),
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddConstraint(
            model_name="userproductionpermission",
            constraint=models.UniqueConstraint(
                fields=("user", "production"), name="uniq_user_production_permission"
            ),
        ),
    ]
