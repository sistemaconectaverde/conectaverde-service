"""Enumerações de domínio compartilhadas (extraídas da planilha oficial de inventário GEE)."""
from django.db import models


class Role(models.TextChoices):
    """Perfis globais de acesso (RBAC)."""

    ADMIN = "ADMIN", "Administrador (Conecta Verde)"
    CONSULTOR = "CONSULTOR", "Consultor"
    PRODUCAO = "PRODUCAO", "Produção (equipe de set)"
    READONLY = "READONLY", "Somente leitura"


class DataStatus(models.TextChoices):
    """Trilha de auditoria: qualidade/origem de cada dado lançado."""

    CONFIRMADO = "CONFIRMADO", "Confirmado (com anexo de NF/MTR)"
    DECLARADO = "DECLARADO", "Declarado (informado pela equipe)"
    ESTIMADO = "ESTIMADO", "Estimado (média estatística)"
    NAO_INFORMADO = "NAO_INFORMADO", "Não informado (lacuna sinalizada)"


class Department(models.TextChoices):
    """Departamentos usados nas abas de transporte da planilha."""

    EQUIPE = "EQUIPE", "Equipe"
    ELENCO = "ELENCO", "Elenco"
    CONVIDADO = "CONVIDADO", "Convidado"
    PLATEIA = "PLATEIA", "Plateia"
    FIGURINO = "FIGURINO", "Figurino"
    MAQUIAGEM = "MAQUIAGEM", "Maquiagem"
    ARTE = "ARTE", "Arte"
    CENARIO = "CENARIO", "Cenário"
    CATERING = "CATERING", "Catering"
    RESIDUOS = "RESIDUOS", "Resíduos"
    EQUIPAMENTOS = "EQUIPAMENTOS", "Equipamentos"
    OUTROS = "OUTROS", "Outros"
