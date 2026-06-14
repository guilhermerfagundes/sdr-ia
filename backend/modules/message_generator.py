"""
Gerador de mensagens de abordagem personalizadas (modo semi-automático).

Cada mensagem usa os dados reais do lead (empresa, cidade, responsável) e o
MOTIVO DE OPORTUNIDADE detectado, para soar escrita à mão — sem parecer robô.

A mensagem é entregue pronta na fila de Abordagem do painel; o usuário abre o
WhatsApp com um clique (link wa.me) e envia manualmente. Nada é enviado sozinho,
respeitando os termos do WhatsApp (sem risco de banir o número).
"""
from __future__ import annotations

import re
import urllib.parse

# Traduz o motivo de oportunidade detectado num "gancho" natural de conversa.
# A ordem importa: o primeiro que casar é usado.
_GANCHOS = [
    ("só instagram", "vi que vocês só têm o Instagram — um site ajudaria a fechar mais"),
    ("sem site informado", "vi que vocês ainda não têm um site, e hoje isso pesa na decisão do cliente"),
    ("fora do ar", "tentei abrir o site de vocês e ele estava fora do ar"),
    ("sem seo", "percebi que o site de vocês quase não aparece nas buscas do Google"),
    ("seo incompleto", "percebi que dá pra fazer o site de vocês aparecer muito mais no Google"),
    ("meta pixel", "notei que vocês ainda não estão fazendo remarketing no Instagram/Facebook"),
    ("anúncios", "vi que vocês ainda não estão anunciando pra atrair clientes novos"),
    ("lento", "reparei que o site de vocês está carregando devagar, o que afasta cliente"),
    ("responsivo", "o site de vocês não está adaptado pro celular, onde a maioria acessa"),
    ("https", "o site de vocês está sem o cadeado de segurança, o que passa desconfiança"),
    ("analytics", "vi que vocês ainda não estão medindo os resultados do site"),
]


_TITULOS = {"dr", "dra", "sr", "sra", "srta", "dro"}


def _primeiro_nome(lead: dict) -> str | None:
    resp = (lead.get("responsavel") or "").strip()
    if not resp:
        return None
    partes = resp.split()
    for p in partes:  # pula títulos como "Dr.", "Dra.", "Sr."
        if p.lower().strip(".") not in _TITULOS:
            return p
    return partes[0]


def gancho_oportunidade(motivo: str | None) -> str:
    m = (motivo or "").lower()
    for chave, frase in _GANCHOS:
        if chave in m:
            return frase
    return "vi que dá pra melhorar bastante a presença digital de vocês na internet"


def gerar_mensagem(lead: dict, cfg: dict | None = None) -> str:
    """Monta a mensagem personalizada de primeiro contato."""
    msg_cfg = (cfg or {}).get("mensagem", {}) if isinstance(cfg, dict) else {}
    remetente = msg_cfg.get("remetente") or "Guilherme"
    cargo = msg_cfg.get("cargo") or "estrategista de marketing"
    proposta = msg_cfg.get("proposta") or "atrair mais clientes pela internet"

    empresa = lead.get("empresa") or "sua empresa"
    cidade = lead.get("cidade") or ""
    nome = _primeiro_nome(lead)
    gancho = gancho_oportunidade(lead.get("oportunidade_motivo"))

    saudacao = f"Oi {nome}! Tudo bem?" if nome else "Oi! Tudo bem?"
    na_cidade = f" aí em {cidade}" if cidade else ""

    return (
        f"{saudacao} 👋\n\n"
        f"Aqui é o {remetente}, {cargo}. Encontrei a *{empresa}*{na_cidade} e {gancho}.\n\n"
        f"Ajudo negócios como o seu a {proposta} — posso te mandar 2 ou 3 ideias "
        f"rápidas e sem compromisso? 😊"
    )


def link_whatsapp(lead: dict, mensagem: str) -> str | None:
    """Gera o link que abre a conversa no WhatsApp Web com a mensagem já digitada.
    Usa web.whatsapp.com/send (vai direto pro chat, sem página intermediária).
    Devolve None se o lead não tiver telefone/WhatsApp."""
    bruto = lead.get("whatsapp") or lead.get("telefone") or ""
    tel = re.sub(r"\D", "", bruto)
    if not tel or len(tel) < 10:
        return None
    if not tel.startswith("55"):
        tel = "55" + tel
    return f"https://web.whatsapp.com/send?phone={tel}&text={urllib.parse.quote(mensagem)}"
