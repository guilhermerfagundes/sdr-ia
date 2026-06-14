"""Testa o gerador de mensagens de abordagem (funções puras)."""
from backend.modules import message_generator as mg


def test_mensagem_personalizada_com_nome_e_oportunidade():
    lead = {
        "empresa": "Clínica Sorriso",
        "responsavel": "Dra. Marina Alves",
        "cidade": "Osasco",
        "segmento": "dentista",
        "oportunidade_motivo": "Site praticamente sem SEO (title/description/H1 ausentes)",
    }
    cfg = {"mensagem": {"remetente": "Gui", "cargo": "estrategista de marketing", "proposta": "atrair clientes"}}
    msg = mg.gerar_mensagem(lead, cfg)
    assert "Marina" in msg                      # usa o primeiro nome
    assert "Clínica Sorriso" in msg              # cita a empresa
    assert "Gui" in msg                          # assina com o remetente
    assert "estrategista de marketing" in msg    # cargo, não agência
    assert "Google" in msg                       # gancho do SEO


def test_mensagem_sem_responsavel():
    lead = {"empresa": "Studio X", "oportunidade_motivo": "Sem site informado"}
    msg = mg.gerar_mensagem(lead, {})
    assert "Studio X" in msg
    assert msg.startswith("Oi! Tudo bem?")


def test_link_whatsapp_normaliza_numero():
    lead = {"telefone": "(11) 98888-0001"}
    link = mg.link_whatsapp(lead, "olá mundo")
    assert link.startswith("https://web.whatsapp.com/send?phone=5511988880001&text=")
    assert "ol%C3%A1" in link  # mensagem url-encoded


def test_link_whatsapp_ja_com_55():
    lead = {"whatsapp": "+55 11 3605-1200"}
    link = mg.link_whatsapp(lead, "x")
    assert link.startswith("https://web.whatsapp.com/send?phone=551136051200&text=")


def test_link_whatsapp_sem_numero():
    assert mg.link_whatsapp({"empresa": "Sem Tel"}, "x") is None
