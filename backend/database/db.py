"""
Camada de banco baseada em SQLAlchemy.

O schema é definido em Python (MetaData) — assim o MESMO código gera as
tabelas corretas tanto no SQLite (uso local) quanto no PostgreSQL (nuvem).
A escolha do banco vem de config.database_url() (DATABASE_URL → Postgres;
senão → SQLite local).
"""
from __future__ import annotations

from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from backend.config import config

metadata = MetaData()

leads = Table(
    "leads",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("data_captura", Text),
    Column("empresa", Text),
    Column("responsavel", Text),
    Column("telefone", Text),
    Column("telefone_norm", Text, index=True),
    Column("whatsapp", Text),
    Column("instagram", Text),
    Column("instagram_norm", Text, index=True),
    Column("email", Text),
    Column("site", Text),
    Column("dominio", Text, index=True),
    Column("cidade", Text),
    Column("estado", Text),
    Column("segmento", Text),
    Column("origem", Text),
    Column("score", Integer, default=0),
    Column("score_justificativa", Text),
    Column("oportunidade_motivo", Text),
    Column("status", Text, default="Novo Lead", index=True),
    Column("ultima_acao", Text),
    Column("proxima_acao", Text),
    Column("dados_enriquecimento", Text),
    Column("created_at", Text),
    Column("updated_at", Text),
)

eventos_log = Table(
    "eventos_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("momento", Text),
    Column("tipo", Text, index=True),
    Column("lead_id", Integer),
    Column("mensagem", Text),
    Column("detalhe", Text),
)

config_runs = Table(
    "config_runs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("momento", Text),
    Column("segmento", Text),
    Column("cidade", Text),
    Column("estado", Text),
    Column("encontrados", Integer),
    Column("novos", Integer),
    Column("atualizados", Integer),
    Column("descartados", Integer),
)


def get_engine(url: str | None = None) -> Engine:
    """Cria o engine SQLAlchemy. Para SQLite em memória (testes), usa um pool
    estático para que todas as conexões compartilhem o mesmo banco."""
    url = url or config.database_url()
    kwargs: dict = {"future": True, "pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in url or url == "sqlite://":
            kwargs["poolclass"] = StaticPool
    return create_engine(url, **kwargs)


def init_db(engine: Engine | None = None) -> Engine:
    """Cria as tabelas se não existirem (idempotente). Devolve o engine."""
    if engine is None:
        engine = get_engine()
    metadata.create_all(engine)
    return engine
