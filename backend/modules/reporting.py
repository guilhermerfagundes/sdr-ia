"""
Relatório diário: consolida os números do dia e salva um arquivo .md em
reports/. Também devolve um dicionário para o dashboard exibir.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.engine import Engine

from backend.config import config
from backend.database import repository
from backend.database.db import leads


def coletar_metricas(engine: Engine, dia: str | None = None) -> dict:
    """Métricas do dia informado (YYYY-MM-DD). Padrão: hoje."""
    dia = dia or date.today().isoformat()
    score_min = config.get_config().get("scoring", {}).get("score_minimo", 40)

    # created_at é ISO "YYYY-MM-DDThh:mm:ss"; o prefixo funciona em SQLite e Postgres
    encontrados_hoje = repository.contar(engine, leads.c.created_at.like(f"{dia}%"))
    qualificados = repository.contar(engine, leads.c.status.notin_(["Novo Lead", "Perdido"]))

    por_status = repository.contar_por_status(engine)
    por_segmento = repository.contar_por_segmento(engine)

    return {
        "dia": dia,
        "total_leads": repository.contar(engine),
        "encontrados_hoje": encontrados_hoje,
        "qualificados": qualificados,
        "acima_do_score_minimo": repository.contar(engine, leads.c.score >= score_min),
        "reunioes_agendadas": por_status.get("Reunião Agendada", 0),
        "propostas": por_status.get("Proposta", 0),
        "fechados": por_status.get("Fechado", 0),
        "perdidos": por_status.get("Perdido", 0),
        "por_status": por_status,
        "por_segmento": por_segmento,
        "score_minimo": score_min,
    }


def _montar_markdown(m: dict) -> str:
    linhas = [
        f"# Relatório Diário — {m['dia']}",
        f"_Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}_",
        "",
        "## Resumo",
        f"- Total de leads na base: **{m['total_leads']}**",
        f"- Encontrados hoje: **{m['encontrados_hoje']}**",
        f"- Qualificados (no pipeline): **{m['qualificados']}**",
        f"- Acima do score mínimo ({m['score_minimo']}): **{m['acima_do_score_minimo']}**",
        f"- Reuniões agendadas: **{m['reunioes_agendadas']}**",
        f"- Propostas: **{m['propostas']}**",
        f"- Fechados: **{m['fechados']}**",
        f"- Perdidos: **{m['perdidos']}**",
        "",
        "## Pipeline (por status)",
    ]
    for status, n in m["por_status"].items():
        linhas.append(f"- {status}: {n}")
    linhas += ["", "## Por segmento"]
    for seg, n in m["por_segmento"].items():
        linhas.append(f"- {seg}: {n}")
    return "\n".join(linhas) + "\n"


def gerar_relatorio_diario(engine: Engine, dia: str | None = None) -> dict:
    """Gera as métricas, salva o .md em reports/ e devolve as métricas + caminho."""
    config.ensure_dirs()
    m = coletar_metricas(engine, dia)
    caminho = config.REPORTS_DIR / f"relatorio_{m['dia']}.md"
    caminho.write_text(_montar_markdown(m), encoding="utf-8")
    m["arquivo"] = str(caminho)
    repository.registrar_evento(engine, "sistema", f"Relatório diário gerado: {caminho.name}")
    return m
