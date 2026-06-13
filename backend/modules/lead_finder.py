"""
Captação de leads.

Duas fontes:
  1. buscar_google_places(...) — Google Maps via Places API oficial (paga,
     estável, legal). Precisa de GOOGLE_PLACES_API_KEY no .env.
  2. importar_csv(...) — ingere uma planilha que você já tem.

Em ambos os casos, cada lead passa pelo MESMO pipeline antes de ser salvo:
  exclusões (ICP) → enriquecimento do site → scoring → oportunidade → dedup.
"""
from __future__ import annotations

import csv
from datetime import date

import requests
from sqlalchemy.engine import Engine

from backend.config import config
from backend.database import repository
from backend.modules import lead_enrichment, lead_scoring, opportunity
from backend.modules.error_handler import get_logger, retry

PLACES_TEXTSEARCH = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS = "https://maps.googleapis.com/maps/api/place/details/json"
logger = get_logger()


# ---- Filtro de ICP (exclusões) ---------------------------------------------


def _deve_excluir(nome: str, categorias: str = "") -> bool:
    palavras = config.get_config().get("exclusoes", {}).get("palavras_chave", [])
    alvo = f"{nome} {categorias}".lower()
    return any(p.lower() in alvo for p in palavras if p)


# ---- Pipeline comum de processamento de um lead ----------------------------


def processar_lead(engine: Engine, lead: dict, enriquecer: bool = True) -> tuple[int | None, str]:
    """
    Aplica exclusão → enriquecimento → score → oportunidade → dedup/salvar.
    Devolve (lead_id, acao) com acao ∈ {"novo","atualizado","descartado"}.
    """
    if _deve_excluir(lead.get("empresa", ""), lead.get("segmento", "")):
        repository.registrar_evento(
            engine, "captacao", f"Descartado por exclusão: {lead.get('empresa')}"
        )
        return None, "descartado"

    if enriquecer:
        sinais = lead_enrichment.enriquecer(lead.get("site"))
    else:
        # Importado sem análise: não inventamos sinais que não verificamos.
        sinais = {"sem_site": not bool(lead.get("site")), "nao_analisado": True}
    lead["dados_enriquecimento"] = {
        "sinais": sinais,
        "resumo": lead_enrichment.gerar_resumo(sinais),
    }
    score, justificativa = lead_scoring.calcular_score(sinais, lead)
    lead["score"] = score
    lead["score_justificativa"] = justificativa
    lead["oportunidade_motivo"] = opportunity.gerar_motivo_abordagem(sinais, lead)
    lead.setdefault("data_captura", date.today().isoformat())

    lead_id, acao = repository.upsert_lead(engine, lead)
    repository.registrar_evento(
        engine, "captacao", f"Lead {acao}: {lead.get('empresa')} (score {score})", lead_id=lead_id
    )
    return lead_id, acao


# ---- Google Places ---------------------------------------------------------


@retry(tentativas=3, espera_seg=2.0, excecoes=(requests.RequestException,))
def _places_textsearch(query: str) -> list[dict]:
    resp = requests.get(
        PLACES_TEXTSEARCH,
        params={"query": query, "key": config.google_places_key(), "language": "pt-BR"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    status = data.get("status")
    if status not in ("OK", "ZERO_RESULTS"):
        raise RuntimeError(f"Places TextSearch retornou status={status}: {data.get('error_message')}")
    return data.get("results", [])


@retry(tentativas=3, espera_seg=2.0, excecoes=(requests.RequestException,))
def _places_details(place_id: str) -> dict:
    campos = "name,formatted_phone_number,international_phone_number,website,formatted_address,rating,user_ratings_total,types"
    resp = requests.get(
        PLACES_DETAILS,
        params={
            "place_id": place_id,
            "fields": campos,
            "key": config.google_places_key(),
            "language": "pt-BR",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("result", {})


def buscar_google_places(
    engine: Engine,
    segmento: str,
    cidade: str,
    estado: str = "",
    limite: int = 20,
) -> dict:
    """
    Busca empresas no Google Maps e salva os leads.
    Devolve um resumo: {encontrados, novos, atualizados, descartados}.
    """
    if not config.tem_chave_google():
        raise RuntimeError(
            "GOOGLE_PLACES_API_KEY não configurada. Use a importação de CSV ou "
            "configure a chave no arquivo .env (veja GUIA-INSTALACAO.md)."
        )

    query = f"{segmento} em {cidade} {estado}".strip()
    logger.info("Buscando no Google Places: %s", query)
    resultados = _places_textsearch(query)[:limite]

    resumo = {"encontrados": len(resultados), "novos": 0, "atualizados": 0, "descartados": 0}

    for r in resultados:
        place_id = r.get("place_id")
        det = _places_details(place_id) if place_id else {}
        tipos = ", ".join(det.get("types", r.get("types", [])))
        lead = {
            "empresa": det.get("name") or r.get("name"),
            "telefone": det.get("formatted_phone_number")
            or det.get("international_phone_number"),
            "site": det.get("website"),
            "cidade": cidade,
            "estado": estado,
            "segmento": segmento,
            "origem": "Google Maps",
        }
        _, acao = processar_lead(engine, lead)
        if acao == "novo":
            resumo["novos"] += 1
        elif acao == "atualizado":
            resumo["atualizados"] += 1
        elif acao == "descartado":
            resumo["descartados"] += 1

    repository.registrar_run(engine, segmento=segmento, cidade=cidade, estado=estado, **resumo)
    logger.info("Resultado da busca '%s': %s", query, resumo)
    return resumo


# ---- Importação de CSV ------------------------------------------------------

# Mapeia variações de cabeçalho de coluna para o nome interno do campo
_ALIASES = {
    "empresa": ["empresa", "nome", "razao social", "razão social", "nome empresa", "company"],
    "responsavel": ["responsavel", "responsável", "contato", "nome contato"],
    "telefone": ["telefone", "fone", "tel", "phone", "celular"],
    "whatsapp": ["whatsapp", "whats", "zap"],
    "instagram": ["instagram", "insta", "ig", "@"],
    "email": ["email", "e-mail", "mail"],
    "site": ["site", "website", "url", "www"],
    "cidade": ["cidade", "city", "municipio", "município"],
    "estado": ["estado", "uf", "state"],
    "segmento": ["segmento", "nicho", "categoria", "ramo"],
}


def _mapear_colunas(cabecalho: list[str]) -> dict[str, str]:
    """Descobre qual coluna do CSV corresponde a cada campo interno."""
    mapa: dict[str, str] = {}
    norm = {c: c.strip().lower() for c in cabecalho}
    for campo, aliases in _ALIASES.items():
        for col, low in norm.items():
            if low in aliases:
                mapa[campo] = col
                break
    return mapa


def importar_csv(
    engine: Engine,
    caminho: str,
    origem: str = "CSV importado",
    enriquecer: bool = True,
) -> dict:
    """Importa um CSV de leads. Detecta automaticamente as colunas comuns."""
    resumo = {"encontrados": 0, "novos": 0, "atualizados": 0, "descartados": 0}

    with open(caminho, newline="", encoding="utf-8-sig") as f:
        # detecta separador (vírgula ou ponto-e-vírgula)
        amostra = f.read(2048)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(amostra, delimiters=",;")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        mapa = _mapear_colunas(reader.fieldnames or [])
        if "empresa" not in mapa:
            raise ValueError(
                "Não encontrei uma coluna de nome da empresa no CSV. "
                "Inclua uma coluna chamada 'empresa' (ou 'nome')."
            )

        for linha in reader:
            resumo["encontrados"] += 1
            lead = {campo: (linha.get(col) or "").strip() for campo, col in mapa.items()}
            lead["origem"] = origem
            if not lead.get("empresa"):
                resumo["descartados"] += 1
                continue
            _, acao = processar_lead(engine, lead, enriquecer=enriquecer)
            if acao == "novo":
                resumo["novos"] += 1
            elif acao == "atualizado":
                resumo["atualizados"] += 1
            elif acao == "descartado":
                resumo["descartados"] += 1

    repository.registrar_run(engine, segmento="(csv)", cidade="(csv)", estado="", **resumo)
    logger.info("Importação de CSV '%s': %s", caminho, resumo)
    return resumo
