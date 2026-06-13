"""
Enriquecimento de leads pela análise do SITE (via HTTP simples — sem scraping
de Instagram/LinkedIn, que violaria os termos dessas plataformas).

A análise é dividida em duas partes para facilitar os testes:
- analisar_html(html, ...): função PURA que extrai os sinais de um HTML dado.
- enriquecer(url): baixa o HTML e chama analisar_html.

Sinais detectados:
  https, tempo_resposta_seg, status_ok, tem_title, tem_meta_description,
  tem_h1, tem_viewport (responsivo), tem_meta_pixel, tem_google_analytics,
  tem_google_ads, qtd_palavras.
"""
from __future__ import annotations

import time

import requests
from bs4 import BeautifulSoup

from backend.modules.error_handler import get_logger, retry

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
TIMEOUT = 12


def _contem(html_lower: str, *agulhas: str) -> bool:
    return any(a in html_lower for a in agulhas)


def analisar_html(
    html: str,
    url: str = "",
    tempo_resposta_seg: float = 0.0,
    status_ok: bool = True,
) -> dict:
    """Extrai sinais de um HTML. Função pura (não acessa a rede)."""
    soup = BeautifulSoup(html or "", "html.parser")
    low = (html or "").lower()

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    h1 = soup.find("h1")
    viewport = soup.find("meta", attrs={"name": "viewport"})
    texto = soup.get_text(" ", strip=True)

    return {
        "url": url,
        "https": url.lower().startswith("https://"),
        "status_ok": status_ok,
        "tempo_resposta_seg": round(tempo_resposta_seg, 2),
        "tem_title": bool(title),
        "title": title,
        "tem_meta_description": meta_desc is not None
        and bool(meta_desc.get("content", "").strip()),
        "tem_h1": h1 is not None and bool(h1.get_text(strip=True)),
        "tem_viewport": viewport is not None,  # indício de site responsivo
        "tem_meta_pixel": _contem(low, "connect.facebook.net", "fbq(", "facebook pixel"),
        "tem_google_analytics": _contem(
            low, "google-analytics.com", "googletagmanager.com", "gtag(", "ga("
        ),
        "tem_google_ads": _contem(low, "googleadservices.com", "aw-", "google_conversion"),
        "qtd_palavras": len(texto.split()),
    }


def _resultado_sem_site() -> dict:
    return {
        "url": "",
        "https": False,
        "status_ok": False,
        "tempo_resposta_seg": 0.0,
        "tem_title": False,
        "title": "",
        "tem_meta_description": False,
        "tem_h1": False,
        "tem_viewport": False,
        "tem_meta_pixel": False,
        "tem_google_analytics": False,
        "tem_google_ads": False,
        "qtd_palavras": 0,
        "sem_site": True,
    }


@retry(tentativas=2, espera_seg=1.5, excecoes=(requests.RequestException,))
def _baixar(url: str) -> tuple[str, float, bool]:
    inicio = time.monotonic()
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    elapsed = time.monotonic() - inicio
    return resp.text, elapsed, resp.ok


def enriquecer(site: str | None) -> dict:
    """Baixa o site e devolve os sinais. Nunca lança exceção: em caso de
    erro, devolve um resultado marcando que o site é inacessível."""
    logger = get_logger()
    if not site or not site.strip():
        return _resultado_sem_site()

    url = site.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        html, elapsed, ok = _baixar(url)
        return analisar_html(html, url=url, tempo_resposta_seg=elapsed, status_ok=ok)
    except Exception as e:  # noqa: BLE001
        logger.warning("Falha ao enriquecer %s: %s", url, e)
        r = _resultado_sem_site()
        r["url"] = url
        r["site_inacessivel"] = True
        return r


def gerar_resumo(sinais: dict) -> str:
    """Resumo automático legível dos sinais do site."""
    if sinais.get("sem_site"):
        return "Lead sem site informado."
    if sinais.get("nao_analisado"):
        return "Site informado, mas ainda não analisado (importado sem enriquecimento)."
    if sinais.get("site_inacessivel"):
        return "Site informado, mas inacessível no momento da análise."

    partes = []
    partes.append("Site no ar" + (" (HTTPS)" if sinais["https"] else " (sem HTTPS)"))
    seo = sum(
        [sinais["tem_title"], sinais["tem_meta_description"], sinais["tem_h1"]]
    )
    partes.append(f"SEO básico {seo}/3")
    partes.append("responsivo" if sinais["tem_viewport"] else "sem viewport")
    rastreio = []
    if sinais["tem_meta_pixel"]:
        rastreio.append("Meta Pixel")
    if sinais["tem_google_analytics"]:
        rastreio.append("Analytics")
    if sinais["tem_google_ads"]:
        rastreio.append("Google Ads")
    partes.append("rastreamento: " + (", ".join(rastreio) if rastreio else "nenhum"))
    if sinais.get("tempo_resposta_seg"):
        partes.append(f"resposta {sinais['tempo_resposta_seg']}s")
    return "; ".join(partes) + "."
