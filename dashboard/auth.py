"""
Login do painel (usuário e senha) usando streamlit-authenticator.

A configuração de credenciais vem de, nesta ordem:
  1. st.secrets["auth"]  → usado no Streamlit Cloud (nuvem)
  2. auth_config.yaml     → usado localmente (gerado por tools/set_password.py)

Se nenhuma existir, o painel orienta a rodar o gerador de senha.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit_authenticator as stauth
import yaml

AUTH_FILE = Path(__file__).resolve().parents[1] / "auth_config.yaml"


def _plain(obj):
    """Converte AttrDict/Secrets aninhados em dict/list puros (mutáveis)."""
    if hasattr(obj, "items"):
        return {k: _plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_plain(v) for v in obj]
    return obj


def _carregar_config() -> dict | None:
    try:
        if "auth" in st.secrets:
            return _plain(st.secrets["auth"])
    except Exception:
        pass
    if AUTH_FILE.exists():
        with open(AUTH_FILE, encoding="utf-8") as f:
            return yaml.safe_load(f)
    return None


def exigir_login():
    """Bloqueia o app até o usuário autenticar. Devolve o objeto authenticator
    (para o botão de logout). Interrompe a renderização se não logado."""
    cfg = _carregar_config()
    if not cfg:
        st.title("🔒 SDR IA")
        st.error(
            "Login ainda não configurado.\n\n"
            "No seu computador, rode uma vez:\n\n"
            "```\npython tools/set_password.py\n```\n\n"
            "para criar seu usuário e senha. (Veja o DEPLOY.md.)"
        )
        st.stop()

    authenticator = stauth.Authenticate(
        cfg["credentials"],
        cfg["cookie"]["name"],
        cfg["cookie"]["key"],
        cfg["cookie"].get("expiry_days", 30),
    )
    authenticator.login(location="main")

    status = st.session_state.get("authentication_status")
    if status is False:
        st.error("Usuário ou senha incorretos.")
        st.stop()
    if status is None:
        st.info("Digite seu usuário e senha para entrar.")
        st.stop()
    return authenticator
