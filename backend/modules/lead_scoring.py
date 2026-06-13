"""
Lead scoring de 0 a 100, com justificativa textual.

Filosofia (do documento de visão): o melhor lead para uma agência de
marketing é a empresa que TEM presença e movimento (logo, fatura e investe),
mas cujo marketing está MAL FEITO (logo, há muito a melhorar e fechar).

  Score ~100: Instagram ativo + site fraco + sem anúncios aparentes
  Score ~80 : Instagram ativo + site mediano
  Score ~50 : pouca presença digital
  Score <40 : não prospectar (sem contato / sem fit)

A função é pura (não acessa rede nem banco) — recebe os sinais já coletados.
"""
from __future__ import annotations


def calcular_score(sinais: dict, lead: dict | None = None) -> tuple[int, str]:
    """Devolve (score 0-100, justificativa)."""
    lead = lead or {}
    pontos = 0
    just: list[str] = []

    # --- Contactabilidade (precisa ter como falar com ele) -------------------
    tem_contato = bool(lead.get("telefone") or lead.get("whatsapp") or lead.get("email"))
    if tem_contato:
        pontos += 15
        just.append("+15 tem contato (telefone/email)")
    else:
        just.append("+0 SEM contato direto (difícil prospectar)")

    # --- Presença digital ----------------------------------------------------
    tem_instagram = bool(lead.get("instagram"))
    if tem_instagram:
        pontos += 25
        just.append("+25 tem Instagram (canal ativo p/ ofertar)")

    tem_site = not sinais.get("sem_site") and not sinais.get("site_inacessivel")
    if tem_site:
        pontos += 10
        just.append("+10 tem site no ar")

    # --- Qualidade do marketing atual (quanto pior, mais oportunidade) -------
    # Só pontuamos a qualidade se o site foi REALMENTE analisado. Sem análise,
    # não fabricamos os bônus de "site fraco".
    if tem_site and not sinais.get("nao_analisado"):
        seo = sum(
            [
                sinais.get("tem_title"),
                sinais.get("tem_meta_description"),
                sinais.get("tem_h1"),
            ]
        )
        if seo <= 1:
            pontos += 20
            just.append("+20 site sem SEO (muita oportunidade)")
        elif seo == 2:
            pontos += 10
            just.append("+10 SEO incompleto")

        if not sinais.get("tem_meta_pixel"):
            pontos += 8
            just.append("+8 sem Meta Pixel")
        if not sinais.get("tem_google_analytics"):
            pontos += 5
            just.append("+5 sem Analytics")
        if not sinais.get("tem_google_ads"):
            pontos += 12
            just.append("+12 sem anúncios aparentes")
        if not sinais.get("tem_viewport"):
            pontos += 5
            just.append("+5 site não responsivo")
    elif tem_instagram and not tem_site:
        # tem Instagram mas não tem site = clássica oportunidade
        pontos += 25
        just.append("+25 tem Instagram mas não tem site (oportunidade clara)")

    if sinais.get("nao_analisado") and tem_site:
        just.append("(site ainda não analisado — score pode subir após enriquecimento)")

    score = max(0, min(100, pontos))
    justificativa = f"Score {score}/100: " + "; ".join(just)
    return score, justificativa


def faixa(score: int) -> str:
    if score >= 80:
        return "Quente"
    if score >= 50:
        return "Morno"
    if score >= 40:
        return "Frio"
    return "Não prospectar"
