"""Testa o scoring e o detector de oportunidades."""
from backend.modules import lead_scoring, opportunity

SINAIS_SITE_FRACO = {
    "sem_site": False,
    "site_inacessivel": False,
    "https": False,
    "tem_title": False,
    "tem_meta_description": False,
    "tem_h1": False,
    "tem_viewport": False,
    "tem_meta_pixel": False,
    "tem_google_analytics": False,
    "tem_google_ads": False,
    "tempo_resposta_seg": 1.0,
}

SINAIS_SITE_BOM = {
    "sem_site": False,
    "site_inacessivel": False,
    "https": True,
    "tem_title": True,
    "tem_meta_description": True,
    "tem_h1": True,
    "tem_viewport": True,
    "tem_meta_pixel": True,
    "tem_google_analytics": True,
    "tem_google_ads": True,
    "tempo_resposta_seg": 0.8,
}


def test_score_alto_para_site_fraco_com_instagram():
    lead = {"instagram": "@x", "telefone": "11 99999-0000"}
    score, just = lead_scoring.calcular_score(SINAIS_SITE_FRACO, lead)
    assert score >= 80
    assert "Score" in just
    assert lead_scoring.faixa(score) == "Quente"


def test_score_baixo_sem_contato_site_bom():
    lead = {}  # sem contato, sem instagram
    score, _ = lead_scoring.calcular_score(SINAIS_SITE_BOM, lead)
    assert score < 40
    assert lead_scoring.faixa(score) == "Não prospectar"


def test_score_limitado_a_100():
    lead = {"instagram": "@x", "telefone": "1", "email": "a@a.com"}
    score, _ = lead_scoring.calcular_score(SINAIS_SITE_FRACO, lead)
    assert 0 <= score <= 100


def test_oportunidades_site_fraco():
    motivos = opportunity.detectar_oportunidades(SINAIS_SITE_FRACO)
    assert any("SEO" in m for m in motivos)
    assert any("anúncios" in m for m in motivos)


def test_oportunidade_sem_site():
    motivos = opportunity.detectar_oportunidades({"sem_site": True}, {"instagram": "@x"})
    assert motivos
    assert "site" in motivos[0].lower()


def test_motivo_abordagem_limita_3():
    motivo = opportunity.gerar_motivo_abordagem(SINAIS_SITE_FRACO)
    assert motivo.count("|") <= 2
