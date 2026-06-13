"""
CRM: estágios do pipeline e transições de status.

Pipeline (do documento de visão):
  Novo Lead → Qualificado → Contato Enviado → Follow-up 1 → Follow-up 2 →
  Respondeu → Reunião Agendada → Reunião Realizada → Proposta → Fechado
  (e "Perdido" pode ser atingido de qualquer estágio).
"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from backend.database import repository

PIPELINE = [
    "Novo Lead",
    "Qualificado",
    "Contato Enviado",
    "Follow-up 1",
    "Follow-up 2",
    "Respondeu",
    "Reunião Agendada",
    "Reunião Realizada",
    "Proposta",
    "Fechado",
]
PERDIDO = "Perdido"
TODOS_STATUS = PIPELINE + [PERDIDO]


def transicoes_validas(status_atual: str) -> list[str]:
    """A partir do estágio atual, para onde se pode ir."""
    if status_atual == "Fechado":
        return []  # estado final
    if status_atual == PERDIDO:
        return ["Novo Lead"]  # reabrir
    destinos: list[str] = []
    if status_atual in PIPELINE:
        idx = PIPELINE.index(status_atual)
        # pode avançar para qualquer estágio seguinte (pula etapas se preciso)
        destinos.extend(PIPELINE[idx + 1 :])
    destinos.append(PERDIDO)
    return destinos


def mover_status(
    engine: Engine, lead_id: int, novo_status: str, nota: str | None = None
) -> bool:
    """Move o lead para um novo status, validando a transição. Loga o evento."""
    lead = repository.obter_lead(engine, lead_id)
    if lead is None:
        return False
    atual = lead["status"] or "Novo Lead"
    if novo_status not in TODOS_STATUS:
        raise ValueError(f"Status inválido: {novo_status}")
    if novo_status != atual and novo_status not in transicoes_validas(atual):
        raise ValueError(f"Transição inválida: {atual} → {novo_status}")

    repository.atualizar_campos(
        engine, lead_id, {"status": novo_status, "ultima_acao": f"Status: {novo_status}"}
    )
    repository.registrar_evento(
        engine, "crm", f"{atual} → {novo_status}", lead_id=lead_id, detalhe=nota
    )
    return True
