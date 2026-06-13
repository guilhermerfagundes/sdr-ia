"""
Camada de acesso a dados (CRUD) + regra de deduplicação.

REGRA DE DUPLICIDADE (do documento de visão):
nunca inserir um novo lead se já existir outro com o MESMO:
  - telefone (normalizado, só dígitos), OU
  - domínio do site, OU
  - @instagram (handle normalizado), OU
  - empresa + cidade.
Quando há duplicata, o registro existente é ATUALIZADO (merge de campos
vazios), em vez de criar outro.

Implementado com SQLAlchemy Core para funcionar igual em SQLite (local) e
PostgreSQL (nuvem). Todas as funções recebem o `engine` como 1º argumento.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy import func, insert, select, update
from sqlalchemy.engine import Engine

from backend.database.db import config_runs, eventos_log, leads

# ---- Normalizadores usados na deduplicação ---------------------------------


def normalizar_telefone(telefone: str | None) -> str:
    if not telefone:
        return ""
    return re.sub(r"\D", "", telefone)


def extrair_dominio(site: str | None) -> str:
    if not site:
        return ""
    s = site.strip().lower()
    if not s:
        return ""
    if not s.startswith(("http://", "https://")):
        s = "http://" + s
    netloc = urlparse(s).netloc
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def normalizar_instagram(instagram: str | None) -> str:
    if not instagram:
        return ""
    s = instagram.strip().lower()
    s = re.sub(r"https?://(www\.)?instagram\.com/", "", s)
    s = s.strip("/@ ")
    s = s.split("?")[0].split("/")[0]
    return s


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ---- Deduplicação -----------------------------------------------------------


def encontrar_duplicata(engine: Engine, lead: dict) -> dict | None:
    """Devolve o lead existente que colide com `lead`, ou None."""
    tel = normalizar_telefone(lead.get("telefone") or lead.get("whatsapp"))
    dom = extrair_dominio(lead.get("site"))
    ig = normalizar_instagram(lead.get("instagram"))
    empresa = (lead.get("empresa") or "").strip().lower()
    cidade = (lead.get("cidade") or "").strip().lower()

    with engine.connect() as conn:
        if tel:
            row = conn.execute(
                select(leads).where(leads.c.telefone_norm == tel).limit(1)
            ).mappings().first()
            if row:
                return dict(row)
        if dom:
            row = conn.execute(
                select(leads).where(leads.c.dominio == dom).limit(1)
            ).mappings().first()
            if row:
                return dict(row)
        if ig:
            row = conn.execute(
                select(leads).where(leads.c.instagram_norm == ig).limit(1)
            ).mappings().first()
            if row:
                return dict(row)
        if empresa:
            row = conn.execute(
                select(leads)
                .where(
                    func.lower(leads.c.empresa) == empresa,
                    func.lower(func.coalesce(leads.c.cidade, "")) == cidade,
                )
                .limit(1)
            ).mappings().first()
            if row:
                return dict(row)
    return None


# Colunas que o chamador pode preencher num lead
_CAMPOS = [
    "data_captura", "empresa", "responsavel", "telefone", "whatsapp",
    "instagram", "email", "site", "cidade", "estado", "segmento", "origem",
    "score", "score_justificativa", "oportunidade_motivo", "status",
    "ultima_acao", "proxima_acao", "dados_enriquecimento",
]


def _preparar(lead: dict) -> dict:
    """Normaliza e serializa os campos derivados antes de gravar."""
    d = {k: lead.get(k) for k in _CAMPOS}
    if isinstance(d.get("dados_enriquecimento"), (dict, list)):
        d["dados_enriquecimento"] = json.dumps(d["dados_enriquecimento"], ensure_ascii=False)
    d["telefone_norm"] = normalizar_telefone(lead.get("telefone") or lead.get("whatsapp"))
    d["dominio"] = extrair_dominio(lead.get("site"))
    d["instagram_norm"] = normalizar_instagram(lead.get("instagram"))
    if not d.get("data_captura"):
        d["data_captura"] = _agora()
    if not d.get("status"):
        d["status"] = "Novo Lead"
    if d.get("score") is None:
        d["score"] = 0
    return d


def inserir_lead(engine: Engine, lead: dict) -> int:
    d = _preparar(lead)
    agora = _agora()
    d["created_at"] = agora
    d["updated_at"] = agora
    with engine.begin() as conn:
        result = conn.execute(insert(leads).values(**d))
        return int(result.inserted_primary_key[0])


def _merge_vazios(existente: dict, novo: dict) -> dict:
    """Preenche apenas os campos que estão vazios no registro existente."""
    atualizacoes = {}
    for campo in _CAMPOS + ["telefone_norm", "dominio", "instagram_norm"]:
        novo_valor = novo.get(campo)
        if novo_valor in (None, ""):
            continue
        atual = existente.get(campo)
        if atual in (None, "", 0):
            atualizacoes[campo] = novo_valor
    return atualizacoes


def upsert_lead(engine: Engine, lead: dict) -> tuple[int, str]:
    """
    Insere o lead ou atualiza o existente (dedup).
    Devolve (lead_id, acao) onde acao ∈ {"novo", "atualizado"}.
    """
    dup = encontrar_duplicata(engine, lead)
    if dup is None:
        return inserir_lead(engine, lead), "novo"

    preparado = _preparar(lead)
    atualizacoes = _merge_vazios(dup, preparado)
    if atualizacoes:
        atualizacoes["updated_at"] = _agora()
        with engine.begin() as conn:
            conn.execute(update(leads).where(leads.c.id == dup["id"]).values(**atualizacoes))
    return int(dup["id"]), "atualizado"


# ---- Consultas e atualizações gerais ---------------------------------------


def atualizar_campos(engine: Engine, lead_id: int, campos: dict) -> None:
    if not campos:
        return
    campos = dict(campos)
    campos["updated_at"] = _agora()
    with engine.begin() as conn:
        conn.execute(update(leads).where(leads.c.id == lead_id).values(**campos))


def obter_lead(engine: Engine, lead_id: int) -> dict | None:
    with engine.connect() as conn:
        row = conn.execute(select(leads).where(leads.c.id == lead_id)).mappings().first()
        return dict(row) if row else None


def listar_leads(
    engine: Engine,
    status: str | None = None,
    segmento: str | None = None,
    score_min: int | None = None,
) -> list[dict]:
    stmt = select(leads)
    if status:
        stmt = stmt.where(leads.c.status == status)
    if segmento:
        stmt = stmt.where(leads.c.segmento == segmento)
    if score_min is not None:
        stmt = stmt.where(leads.c.score >= score_min)
    stmt = stmt.order_by(leads.c.score.desc(), leads.c.created_at.desc())
    with engine.connect() as conn:
        return [dict(r) for r in conn.execute(stmt).mappings().all()]


def contar_por_status(engine: Engine) -> dict[str, int]:
    stmt = select(leads.c.status, func.count().label("n")).group_by(leads.c.status)
    with engine.connect() as conn:
        return {r["status"]: r["n"] for r in conn.execute(stmt).mappings().all()}


def contar_por_segmento(engine: Engine) -> dict[str, int]:
    seg = func.coalesce(leads.c.segmento, "(sem segmento)").label("s")
    stmt = select(seg, func.count().label("n")).group_by(seg).order_by(func.count().desc())
    with engine.connect() as conn:
        return {r["s"]: r["n"] for r in conn.execute(stmt).mappings().all()}


def contar(engine: Engine, *condicoes) -> int:
    """Conta leads que satisfazem as condições SQLAlchemy passadas."""
    stmt = select(func.count()).select_from(leads)
    for c in condicoes:
        stmt = stmt.where(c)
    with engine.connect() as conn:
        return int(conn.execute(stmt).scalar() or 0)


# ---- Log de eventos ---------------------------------------------------------


def registrar_evento(
    engine: Engine,
    tipo: str,
    mensagem: str,
    lead_id: int | None = None,
    detalhe: str | None = None,
) -> None:
    with engine.begin() as conn:
        conn.execute(
            insert(eventos_log).values(
                momento=_agora(), tipo=tipo, lead_id=lead_id, mensagem=mensagem, detalhe=detalhe
            )
        )


def registrar_run(engine: Engine, **kwargs) -> None:
    with engine.begin() as conn:
        conn.execute(
            insert(config_runs).values(
                momento=_agora(),
                segmento=kwargs.get("segmento"),
                cidade=kwargs.get("cidade"),
                estado=kwargs.get("estado"),
                encontrados=kwargs.get("encontrados", 0),
                novos=kwargs.get("novos", 0),
                atualizados=kwargs.get("atualizados", 0),
                descartados=kwargs.get("descartados", 0),
            )
        )
