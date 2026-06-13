"""Testa a regra de deduplicação do repositório."""
from backend.database import repository as repo


def test_normalizadores():
    assert repo.normalizar_telefone("(11) 99876-5432") == "11998765432"
    assert repo.extrair_dominio("https://www.Exemplo.com.br/contato") == "exemplo.com.br"
    assert repo.normalizar_instagram("https://instagram.com/Minha.Clinica/") == "minha.clinica"
    assert repo.normalizar_instagram("@Minha.Clinica") == "minha.clinica"


def test_insere_novo(engine):
    lead_id, acao = repo.upsert_lead(engine, {"empresa": "Clínica A", "cidade": "Osasco", "telefone": "11 99999-0000"})
    assert acao == "novo"
    assert lead_id > 0


def test_dedup_por_telefone(engine):
    repo.upsert_lead(engine, {"empresa": "Clínica A", "telefone": "(11) 99999-0000"})
    _, acao = repo.upsert_lead(engine, {"empresa": "Clínica A LTDA", "telefone": "11999990000"})
    assert acao == "atualizado"
    assert len(repo.listar_leads(engine)) == 1


def test_dedup_por_dominio(engine):
    repo.upsert_lead(engine, {"empresa": "Empresa X", "site": "https://x.com.br"})
    _, acao = repo.upsert_lead(engine, {"empresa": "Empresa X filial", "site": "http://www.x.com.br/home"})
    assert acao == "atualizado"
    assert len(repo.listar_leads(engine)) == 1


def test_dedup_por_instagram(engine):
    repo.upsert_lead(engine, {"empresa": "Loja Y", "instagram": "@loja.y"})
    _, acao = repo.upsert_lead(engine, {"empresa": "Loja Y", "instagram": "instagram.com/loja.y"})
    assert acao == "atualizado"


def test_dedup_por_empresa_cidade(engine):
    repo.upsert_lead(engine, {"empresa": "Dr. João", "cidade": "Barueri"})
    _, acao = repo.upsert_lead(engine, {"empresa": "dr. joão", "cidade": "barueri"})
    assert acao == "atualizado"


def test_merge_preenche_vazios(engine):
    lead_id, _ = repo.upsert_lead(engine, {"empresa": "Z", "telefone": "11 3000-0000"})
    repo.upsert_lead(engine, {"empresa": "Z", "telefone": "1130000000", "email": "z@z.com"})
    atualizado = repo.obter_lead(engine, lead_id)
    assert atualizado["email"] == "z@z.com"


def test_empresas_diferentes_nao_deduplicam(engine):
    repo.upsert_lead(engine, {"empresa": "Alpha", "cidade": "Osasco"})
    repo.upsert_lead(engine, {"empresa": "Beta", "cidade": "Osasco"})
    assert len(repo.listar_leads(engine)) == 2
