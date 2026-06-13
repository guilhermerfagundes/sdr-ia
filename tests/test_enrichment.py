"""Testa o parser de enriquecimento (função pura, sem rede)."""
from backend.modules import lead_enrichment

HTML_BOM = """
<html><head>
  <title>Clínica Top</title>
  <meta name="description" content="A melhor clínica">
  <meta name="viewport" content="width=device-width">
  <script src="https://www.googletagmanager.com/gtag/js"></script>
  <script>!function(){fbq('init','123')}();</script>
  <script src="https://connect.facebook.net/en_US/fbevents.js"></script>
</head><body><h1>Bem-vindo</h1><p>conteudo aqui com varias palavras</p></body></html>
"""

HTML_FRACO = "<html><head></head><body>oi</body></html>"


def test_site_completo():
    s = lead_enrichment.analisar_html(HTML_BOM, url="https://clinica.com", status_ok=True)
    assert s["tem_title"]
    assert s["tem_meta_description"]
    assert s["tem_h1"]
    assert s["tem_viewport"]
    assert s["tem_meta_pixel"]
    assert s["tem_google_analytics"]
    assert s["https"]


def test_site_fraco():
    s = lead_enrichment.analisar_html(HTML_FRACO, url="http://fraco.com")
    assert not s["tem_title"]
    assert not s["tem_meta_description"]
    assert not s["tem_meta_pixel"]
    assert not s["https"]


def test_resumo_sem_site():
    assert "sem site" in lead_enrichment.gerar_resumo({"sem_site": True}).lower()
