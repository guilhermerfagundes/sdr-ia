"""
Dashboard do SDR IA (Streamlit) — com login.

Rode com:  streamlit run dashboard/app.py
(ou clique duas vezes em run-dashboard.bat)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

# Garante que os pacotes "backend" e este diretório sejam importáveis
PROJECT_ROOT = Path(__file__).resolve().parents[1]
for p in (str(PROJECT_ROOT), str(Path(__file__).resolve().parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Na nuvem (Streamlit Cloud) os segredos vêm de st.secrets — copiamos para
# variáveis de ambiente ANTES de importar o backend, que as lê de lá.
for _chave in ("DATABASE_URL", "GOOGLE_PLACES_API_KEY"):
    try:
        if _chave in st.secrets:
            os.environ[_chave] = str(st.secrets[_chave])
    except Exception:
        pass

import pandas as pd  # noqa: E402

from auth import exigir_login  # noqa: E402
from backend.config import config  # noqa: E402
from backend.database import db  # noqa: E402
from backend.database import repository  # noqa: E402
from backend.modules import crm, lead_finder, reporting  # noqa: E402

st.set_page_config(page_title="SDR IA — Painel", page_icon="🎯", layout="wide")


@st.cache_resource
def get_engine():
    """Engine do banco (SQLite local ou Postgres na nuvem), criado uma vez."""
    return db.init_db(db.get_engine())


# ---- Login (bloqueia tudo abaixo até autenticar) ---------------------------
authenticator = exigir_login()

engine = get_engine()
cfg = config.get_config()

with st.sidebar:
    st.markdown(f"👤 **{st.session_state.get('name', 'Usuário')}**")
    authenticator.logout("Sair", "sidebar")
    st.caption("Banco: " + ("Postgres (nuvem)" if os.getenv("DATABASE_URL") else "SQLite (local)"))

st.title("🎯 SDR IA — Painel de Prospecção")

if not config.tem_chave_google():
    st.warning(
        "Chave do Google Places **não configurada** — a aba *Buscar leads* fica "
        "indisponível, mas você pode usar tudo via *Importar CSV*."
    )

abas = st.tabs(
    ["📊 Visão geral", "📋 Leads", "🔎 Buscar leads", "📥 Importar CSV", "📈 Relatórios", "⚙️ Configurações"]
)

# ---------------------------------------------------------------- Visão geral
with abas[0]:
    m = reporting.coletar_metricas(engine)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de leads", m["total_leads"])
    c2.metric("Encontrados hoje", m["encontrados_hoje"])
    c3.metric("Qualificados", m["qualificados"])
    c4.metric(f"Acima do score {m['score_minimo']}", m["acima_do_score_minimo"])
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Reuniões agendadas", m["reunioes_agendadas"])
    c6.metric("Propostas", m["propostas"])
    c7.metric("Fechados", m["fechados"])
    c8.metric("Perdidos", m["perdidos"])

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Pipeline por status")
        if m["por_status"]:
            st.bar_chart(pd.Series(m["por_status"], name="leads"))
        else:
            st.info("Sem dados ainda. Comece importando um CSV ou buscando leads.")
    with col_b:
        st.subheader("Por segmento")
        if m["por_segmento"]:
            st.bar_chart(pd.Series(m["por_segmento"], name="leads"))

# ---------------------------------------------------------------------- Leads
with abas[1]:
    st.subheader("Leads na base")
    colf1, colf2, colf3 = st.columns(3)
    f_status = colf1.selectbox("Status", ["(todos)"] + crm.TODOS_STATUS)
    segs = sorted({r["segmento"] for r in repository.listar_leads(engine) if r["segmento"]})
    f_seg = colf2.selectbox("Segmento", ["(todos)"] + segs)
    f_score = colf3.slider("Score mínimo", 0, 100, 0)

    rows = repository.listar_leads(
        engine,
        status=None if f_status == "(todos)" else f_status,
        segmento=None if f_seg == "(todos)" else f_seg,
        score_min=f_score,
    )
    if rows:
        df = pd.DataFrame(rows)[
            ["id", "empresa", "telefone", "site", "cidade", "segmento", "score",
             "status", "oportunidade_motivo"]
        ]
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("#### Mover lead no pipeline")
        ids = [r["id"] for r in rows]
        sel = st.selectbox("Lead", ids, format_func=lambda i: f"#{i} — {repository.obter_lead(engine, i)['empresa']}")
        lead = repository.obter_lead(engine, sel)
        st.caption(f"Status atual: **{lead['status']}** · Score {lead['score']} · {lead['score_justificativa']}")
        destinos = crm.transicoes_validas(lead["status"])
        if destinos:
            novo = st.selectbox("Novo status", destinos)
            nota = st.text_input("Nota (opcional)")
            if st.button("Atualizar status"):
                crm.mover_status(engine, sel, novo, nota or None)
                st.success(f"Lead #{sel} movido para '{novo}'.")
                st.rerun()
        else:
            st.info("Este lead está em estágio final (Fechado).")
    else:
        st.info("Nenhum lead com esses filtros.")

# --------------------------------------------------------------- Buscar leads
with abas[2]:
    st.subheader("Buscar no Google Maps")
    if not config.tem_chave_google():
        st.error("Configure a GOOGLE_PLACES_API_KEY para usar esta aba.")
    else:
        segmentos = cfg.get("segmentos", [])
        cidades = [f"{c['cidade']}/{c['estado']}" for c in cfg.get("cidades", [])]
        cg1, cg2, cg3 = st.columns(3)
        seg = cg1.selectbox("Segmento", segmentos or ["(defina em Configurações)"])
        cidade_sel = cg2.selectbox("Cidade", cidades or ["(defina em Configurações)"])
        limite = cg3.number_input("Máx. de leads", 1, 60, cfg["captacao"]["leads_por_dia"])
        if st.button("🔎 Buscar agora", disabled=not (segmentos and cidades)):
            cidade, estado = (cidade_sel.split("/") + [""])[:2]
            with st.spinner("Buscando e analisando os sites dos leads..."):
                resumo = lead_finder.buscar_google_places(engine, seg, cidade, estado, int(limite))
            st.success(
                f"Encontrados {resumo['encontrados']} · novos {resumo['novos']} · "
                f"atualizados {resumo['atualizados']} · descartados {resumo['descartados']}"
            )

# -------------------------------------------------------------- Importar CSV
with abas[3]:
    st.subheader("Importar leads de um CSV")
    st.caption(
        "Colunas reconhecidas automaticamente: empresa/nome, telefone, whatsapp, "
        "instagram, email, site, cidade, estado, segmento. A coluna de empresa é obrigatória."
    )
    enriquecer = st.checkbox("Analisar o site de cada lead (mais lento, mais completo)", value=True)
    arquivo = st.file_uploader("Arquivo CSV", type=["csv"])
    if arquivo and st.button("📥 Importar"):
        config.ensure_dirs()
        destino = config.DATA_DIR / "ultimo_import.csv"
        destino.write_bytes(arquivo.getbuffer())
        with st.spinner("Importando e processando..."):
            resumo = lead_finder.importar_csv(engine, str(destino), enriquecer=enriquecer)
        st.success(
            f"Linhas {resumo['encontrados']} · novos {resumo['novos']} · "
            f"atualizados {resumo['atualizados']} · descartados {resumo['descartados']}"
        )

# ---------------------------------------------------------------- Relatórios
with abas[4]:
    st.subheader("Relatório diário")
    if st.button("Gerar relatório de hoje"):
        m = reporting.gerar_relatorio_diario(engine)
        st.success(f"Relatório salvo em: {m['arquivo']}")
    arquivos = sorted(config.REPORTS_DIR.glob("relatorio_*.md"), reverse=True) if config.REPORTS_DIR.exists() else []
    if arquivos:
        escolha = st.selectbox("Relatórios gerados", [a.name for a in arquivos])
        st.markdown((config.REPORTS_DIR / escolha).read_text(encoding="utf-8"))
    else:
        st.info("Nenhum relatório gerado ainda.")

# ------------------------------------------------------------- Configurações
with abas[5]:
    st.subheader("Configurações")
    st.caption("Alterações aqui são salvas no config.yaml.")
    cap = cfg["captacao"]
    c1, c2 = st.columns(2)
    leads_dia = c1.number_input("Leads por dia", 1, 500, cap["leads_por_dia"])
    score_min = c2.number_input("Score mínimo", 0, 100, cfg["scoring"]["score_minimo"])
    h1 = c1.text_input("Horário inicial", cap["horario_inicial"])
    h2 = c2.text_input("Horário final", cap["horario_final"])
    segmentos_txt = st.text_area("Segmentos (um por linha)", "\n".join(cfg.get("segmentos", [])))
    cidades_txt = st.text_area(
        "Cidades (formato Cidade,UF — uma por linha)",
        "\n".join(f"{c['cidade']},{c['estado']}" for c in cfg.get("cidades", [])),
    )
    exclusoes_txt = st.text_area(
        "Exclusões (palavras-chave, uma por linha)",
        "\n".join(cfg.get("exclusoes", {}).get("palavras_chave", [])),
    )
    if st.button("💾 Salvar configurações"):
        novo = dict(cfg)
        novo["captacao"]["leads_por_dia"] = int(leads_dia)
        novo["captacao"]["horario_inicial"] = h1
        novo["captacao"]["horario_final"] = h2
        novo["scoring"]["score_minimo"] = int(score_min)
        novo["segmentos"] = [s.strip() for s in segmentos_txt.splitlines() if s.strip()]
        cidades = []
        for linha in cidades_txt.splitlines():
            if "," in linha:
                cidade, uf = linha.split(",", 1)
                cidades.append({"cidade": cidade.strip(), "estado": uf.strip()})
        novo["cidades"] = cidades
        novo["exclusoes"]["palavras_chave"] = [
            s.strip() for s in exclusoes_txt.splitlines() if s.strip()
        ]
        try:
            config.save_config(novo)
            st.success("Configurações salvas! Recarregue a página para ver tudo atualizado.")
        except OSError:
            st.error(
                "Não foi possível salvar (na nuvem o sistema de arquivos é só-leitura). "
                "Edite o config.yaml direto no GitHub para mudar as configurações na versão online."
            )
