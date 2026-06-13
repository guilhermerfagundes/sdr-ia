"""Teste manual de conexão com o Postgres da nuvem (Supabase).

Rode com:  python tests/test_postgres_conn.py
Cria as tabelas, insere um lead de teste, lê de volta e remove.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.config import config
from backend.database import db, repository


def main():
    url = config.database_url()
    destino = "Postgres (nuvem)" if url.startswith("postgresql") else "SQLite (local)"
    print("Conectando em:", destino)
    engine = db.init_db(db.get_engine())
    print("Tabelas criadas/verificadas com sucesso.")

    lead_id, acao = repository.upsert_lead(
        engine, {"empresa": "TESTE CONEXAO", "telefone": "(11) 90000-0000", "cidade": "Teste"}
    )
    print(f"Lead de teste: id={lead_id} acao={acao}")
    lido = repository.obter_lead(engine, lead_id)
    print("Lido de volta:", lido["empresa"], "| status:", lido["status"])

    # limpa o lead de teste
    with engine.begin() as conn:
        from backend.database.db import leads
        conn.execute(leads.delete().where(leads.c.id == lead_id))
    print("Lead de teste removido. ✅ Conexão com o banco funcionando.")


if __name__ == "__main__":
    main()
