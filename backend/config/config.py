"""
Carrega a configuração do sistema:
- variáveis sensíveis do arquivo .env (ex.: chave da Google Places API)
- preferências operacionais do config.yaml (segmentos, cidades, horários, etc.)

Centraliza também os caminhos de pastas usados pelo sistema (banco, logs,
relatórios, exports), criando-os automaticamente quando necessário.
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Raiz do projeto: .../sdr-ia  (este arquivo está em backend/config/config.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Carrega o .env se existir (não falha se não existir)
load_dotenv(PROJECT_ROOT / ".env")

# ---- Caminhos de pastas/arquivos -------------------------------------------
DATA_DIR = PROJECT_ROOT / "data"
EXPORTS_DIR = PROJECT_ROOT / "exports"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"
DB_PATH = DATA_DIR / "sdr.db"
CONFIG_YAML = PROJECT_ROOT / "config.yaml"

# ---- Segredos (lidos de forma dinâmica) -------------------------------------
# Lidos por função (não em constante) para funcionar tanto com .env local
# quanto com os "secrets" do Streamlit Cloud, que o dashboard injeta em
# os.environ antes de importar o backend.


def google_places_key() -> str:
    return os.getenv("GOOGLE_PLACES_API_KEY", "").strip()


def database_url() -> str:
    """URL do banco. Se DATABASE_URL existir (Postgres na nuvem), usa ela;
    senão usa o SQLite local (data/sdr.db)."""
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        # SQLAlchemy precisa do driver explícito para Postgres
        if url.startswith("postgres://"):
            url = "postgresql+psycopg2://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg2://" + url[len("postgresql://"):]
        return url
    ensure_dirs()
    return f"sqlite:///{DB_PATH.as_posix()}"


def ensure_dirs() -> None:
    """Garante que todas as pastas de trabalho existam."""
    for d in (DATA_DIR, EXPORTS_DIR, REPORTS_DIR, LOGS_DIR):
        d.mkdir(parents=True, exist_ok=True)


_DEFAULT_CONFIG = {
    "captacao": {
        "leads_por_dia": 30,
        "dias_semana": ["segunda", "terca", "quarta", "quinta", "sexta"],
        "horario_inicial": "09:00",
        "horario_final": "18:00",
        "intervalo_min_seg": 60,
        "intervalo_max_seg": 300,
    },
    "segmentos": [],
    "cidades": [],
    "scoring": {"score_minimo": 40},
    "exclusoes": {"palavras_chave": []},
}


def get_config() -> dict:
    """Lê o config.yaml. Se não existir, devolve os defaults."""
    if not CONFIG_YAML.exists():
        return dict(_DEFAULT_CONFIG)
    with open(CONFIG_YAML, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # mescla com defaults para não quebrar se faltar alguma chave
    merged = dict(_DEFAULT_CONFIG)
    merged.update(data)
    return merged


def save_config(data: dict) -> None:
    """Salva o config.yaml (usado pela aba Configurações do dashboard)."""
    with open(CONFIG_YAML, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def tem_chave_google() -> bool:
    return bool(google_places_key())
