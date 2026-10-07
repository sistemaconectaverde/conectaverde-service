import uuid

from django.conf import settings
from django.db import models

from apps.core.choices import Department


class Production(models.Model):
    """
    Projeto audiovisual inventariado (série, filme, programa).
    Campos espelham a aba 'INFORMAÇÕES DO PROJETO' da planilha oficial de inventário GEE.
    """

    class Status(models.TextChoices):
        PLANEJADA = "PLANEJADA", "Planejada"
        EM_ANDAMENTO = "EM_ANDAMENTO", "Em andamento"
        EM_AUDITORIA = "EM_AUDITORIA", "Em auditoria"
        CONCLUIDA = "CONCLUIDA", "Concluída"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("nome do projeto", max_length=200)
    code = models.SlugField("código", max_length=60, unique=True)
    client_name = models.CharField("produtora / cliente", max_length=200, blank=True)
    location = models.CharField("local", max_length=200, blank=True)
    city = models.CharField("cidade", max_length=120, blank=True)
    state = models.CharField("UF", max_length=2, blank=True)
    episodes_count = models.PositiveIntegerField("número de episódios", null=True, blank=True)
    shooting_days = models.PositiveIntegerField("dias de filmagem", null=True, blank=True)
    pre_production_days = models.PositiveIntegerField("dias de pré-produção", null=True, blank=True)
    post_production_days = models.PositiveIntegerField("dias de pós-produção", null=True, blank=True)
    start_date = models.DateField("início", null=True, blank=True)
    end_date = models.DateField("término", null=True, blank=True)
    status = models.CharField("status", max_length=20, choices=Status.choices, default=Status.PLANEJADA)
    is_active = models.BooleanField("ativa", default=True)
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="UserProductionPermission",
        through_fields=("production", "user"),
        related_name="productions",
        blank=True,
    )

    class Meta:
        verbose_name = "produção"
        verbose_name_plural = "produções"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class UserProductionPermission(models.Model):
    """
    Vínculo usuário <-> produção (multi-tenant).
    - CONSULTOR: produções sob sua responsabilidade.
    - PRODUCAO: produção + departamento em que pode lançar dados.
    - READONLY: produções que pode visualizar.
    ADMIN enxerga todas as produções e não precisa de vínculo.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="production_permissions"
    )
    production = models.ForeignKey(Production, on_delete=models.CASCADE, related_name="permissions")
    department = models.CharField(
        "departamento", max_length=20, choices=Department.choices, blank=True,
        help_text="Obrigatório na prática para o perfil PRODUCAO (restringe o lançamento ao departamento).",
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="concedido por",
    )
    created_at = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        verbose_name = "permissão em produção"
        verbose_name_plural = "permissões em produções"
        constraints = [
            models.UniqueConstraint(fields=["user", "production"], name="uniq_user_production_permission"),
        ]

    def __str__(self) -> str:
        return f"{self.user} → {self.production}"
