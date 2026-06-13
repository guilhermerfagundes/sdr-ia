"""Teste de fumaça ponta a ponta (manual): importa o CSV de exemplo no banco
real, move um lead no pipeline e gera o relatório. Rode com:

    python tests/smoke_e2e.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.database import db, repository
from backend.modules import crm, lead_finder, reporting

EXEMPLO = Path(__file__).resolve().parents[1] / "exports" / "exemplo_leads.csv"


def main():
    engine = db.init_db(db.get_engine())
    resumo = lead_finder.importar_csv(engine, str(EXEMPLO), enriquecer=False)
    print("Import:", resumo)

    leads = repository.listar_leads(engine)
    print("Total na base:", len(leads))
    for l in leads:
        print(f"  #{l['id']} {l['empresa']} | score={l['score']} | {l['oportunidade_motivo'][:60]}")

    crm.mover_status(engine, leads[0]["id"], "Qualificado")
    m = reporting.gerar_relatorio_diario(engine)
    print("Relatorio salvo em:", m["arquivo"])
    print("Qualificados:", m["qualificados"])


if __name__ == "__main__":
    main()
