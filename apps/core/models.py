"""Modelos abstratos reutilizados por todos os módulos de lançamento (Sprints 2+)."""
import uuid

from django.conf import settings
from django.db import models

from apps.core.choices import DataStatus, Department


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class AuditedRecord(UUIDModel, TimeStampedModel):
    """
    Base para todo registro de emissão (gerador, transporte, resíduos, energia...).

    Atende ao requisito de Governança dos Dados do guia: status do dado,
    origem (usuário/departamento) e metodologia + versão do fator aplicado.
    """

    production = models.ForeignKey(
        "productions.Production", on_delete=models.CASCADE, related_name="%(class)s_records"
    )
    data_status = models.CharField(
        "status do dado", max_length=20, choices=DataStatus.choices, default=DataStatus.DECLARADO
    )
    source_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="lançado por",
    )
    source_department = models.CharField(
        "departamento de origem", max_length=20, choices=Department.choices, blank=True
    )
    methodology = models.CharField("metodologia", max_length=120, blank=True)
    emission_factor_version = models.CharField("versão do fator de emissão", max_length=40, blank=True)
    evidence_url = models.URLField("anexo (NF/MTR)", max_length=500, blank=True)
    notes = models.TextField("comentários", blank=True)

    class Meta:
        abstract = True
