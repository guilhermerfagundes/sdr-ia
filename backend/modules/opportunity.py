"""
Detector de oportunidades: traduz os sinais do enriquecimento em MOTIVOS DE
ABORDAGEM concretos — a "deixa" que o SDR usa para iniciar a conversa.

Ex.: site sem SEO, sem pixel de rastreamento, site lento, sem indícios de
anúncios, ausência de site.
"""
from __future__ import annotations

LIMITE_SITE_LENTO_SEG = 3.0


def detectar_oportunidades(sinais: dict, lead: dict | None = None) -> list[str]:
    """Lista de oportunidades encontradas (texto curto cada uma)."""
    lead = lead or {}
    motivos: list[str] = []

    if sinais.get("sem_site"):
        if lead.get("instagram"):
            motivos.append("Sem site (só Instagram) — oportunidade de presença digital")
        else:
            motivos.append("Sem site informado — oportunidade de presença digital")
        return motivos

    if sinais.get("site_inacessivel"):
        motivos.append("Site fora do ar / inacessível")
        return motivos

    if sinais.get("nao_analisado"):
        motivos.append("Site ainda não analisado — rode o enriquecimento para detalhar oportunidades")
        return motivos

    seo = sum(
        [sinais.get("tem_title"), sinais.get("tem_meta_description"), sinais.get("tem_h1")]
    )
    if seo <= 1:
        motivos.append("Site praticamente sem SEO (title/description/H1 ausentes)")
    elif seo == 2:
        motivos.append("SEO incompleto no site")

    if not sinais.get("https"):
        motivos.append("Site sem HTTPS (cadeado de segurança)")

    if not sinais.get("tem_viewport"):
        motivos.append("Site provavelmente não responsivo (ruim no celular)")

    if not sinais.get("tem_meta_pixel"):
        motivos.append("Sem Meta Pixel — não consegue remarketing no Instagram/Facebook")

    if not sinais.get("tem_google_analytics"):
        motivos.append("Sem Google Analytics — não mede resultado do site")

    if not sinais.get("tem_google_ads"):
        motivos.append("Sem indícios de anúncios (Google Ads)")

    if sinais.get("tempo_resposta_seg", 0) > LIMITE_SITE_LENTO_SEG:
        motivos.append("Site lento para carregar")

    return motivos


def gerar_motivo_abordagem(sinais: dict, lead: dict | None = None) -> str:
    """Frase única e priorizada para usar na abordagem."""
    motivos = detectar_oportunidades(sinais, lead)
    if not motivos:
        return "Sem oportunidade óbvia detectada — avaliar manualmente."
    # mostra até 3 motivos mais relevantes
    return " | ".join(motivos[:3])
