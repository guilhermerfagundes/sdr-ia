"""Testa o pipeline do CRM e a importação de CSV (sem rede: enriquecer=False)."""
from backend.database import repository as repo
from backend.modules import crm, lead_finder


def test_transicoes_validas():
    assert "Qualificado" in crm.transicoes_validas("Novo Lead")
    assert "Perdido" in crm.transicoes_validas("Novo Lead")
    assert crm.transicoes_validas("Fechado") == []


def test_mover_status_valido(engine):
    lead_id, _ = repo.upsert_lead(engine, {"empresa": "Teste"})
    assert crm.mover_status(engine, lead_id, "Qualificado")
    assert repo.obter_lead(engine, lead_id)["status"] == "Qualificado"


def test_mover_status_invalido_levanta(engine):
    lead_id, _ = repo.upsert_lead(engine, {"empresa": "Teste"})
    crm.mover_status(engine, lead_id, "Fechado")
    try:
        crm.mover_status(engine, lead_id, "Novo Lead")
        assert False, "deveria ter levantado"
    except ValueError:
        pass


def test_importar_csv(engine, tmp_path):
    csv_file = tmp_path / "leads.csv"
    csv_file.write_text(
        "empresa,telefone,cidade,segmento\n"
        "Clínica Sorriso,(11) 98888-0001,Osasco,dentista\n"
        "Advocacia Lima,(11) 98888-0002,Barueri,advogado\n"
        "Agência de Marketing XPTO,(11) 98888-0003,Osasco,marketing\n",
        encoding="utf-8",
    )
    resumo = lead_finder.importar_csv(engine, str(csv_file), enriquecer=False)
    assert resumo["encontrados"] == 3
    assert resumo["novos"] == 2          # 2 leads válidos
    assert resumo["descartados"] == 1    # "Agência de Marketing" excluída pelo ICP
    assert len(repo.listar_leads(engine)) == 2


def test_csv_dedup_em_reimport(engine, tmp_path):
    csv_file = tmp_path / "leads.csv"
    csv_file.write_text(
        "empresa,telefone,cidade\nClínica Sorriso,11988880001,Osasco\n", encoding="utf-8"
    )
    lead_finder.importar_csv(engine, str(csv_file), enriquecer=False)
    resumo = lead_finder.importar_csv(engine, str(csv_file), enriquecer=False)
    assert resumo["atualizados"] == 1
    assert len(repo.listar_leads(engine)) == 1
