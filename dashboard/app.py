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

from dashboard.auth import exigir_login  # noqa: E402
from backend.config import config  # noqa: E402
from backend.database import db  # noqa: E402
from backend.database import repository  # noqa: E402
from backend.modules import crm, lead_finder, message_generator, reporting  # noqa: E402

st.set_page_config(page_title="DemandOS AI", page_icon="🧭", layout="wide")

st.markdown(
    """
    <style>
      .block-container { padding-top: 2.2rem; max-width: 1300px; }
      /* Cabeçalho */
      .hero {
        background: linear-gradient(110deg, #1e3a8a 0%, #2563eb 55%, #3b82f6 100%);
        color: #fff; padding: 22px 28px; border-radius: 16px; margin-bottom: 18px;
        box-shadow: 0 8px 24px rgba(37,99,235,.25);
      }
      .hero h1 { color:#fff; font-size: 1.9rem; font-weight: 800; margin: 0; }
      .hero p  { color:#dbeafe; margin: 4px 0 0; font-size: .98rem; }
      /* Cartões de métrica */
      [data-testid="stMetric"] {
        background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px;
        padding: 14px 16px;
      }
      [data-testid="stMetricValue"] { font-size: 1.7rem; font-weight: 700; color:#1e293b; }
      [data-testid="stMetricLabel"] { color:#64748b; }
      /* Abas */
      button[data-baseweb="tab"] { font-size: 1rem; }
      /* Sidebar */
      [data-testid="stSidebar"] { background: #0f172a; }
      [data-testid="stSidebar"] * { color:#e2e8f0 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


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

st.markdown(
    '<div class="hero"><h1>🧭 DemandOS AI</h1>'
    "<p>Seu sistema operacional de geração de demanda</p></div>",
    unsafe_allow_html=True,
)

# Resultado da última busca — mostrado no topo (sempre visível, mesmo que a aba
# volte para "Visão geral" depois de processar).
if "busca_result" in st.session_state:
    r = st.session_state.pop("busca_result")
    st.success(
        f"✅ Busca de **{r['seg']}** em **{r['cidade']}**: encontrados "
        f"{r['encontrados']} · novos {r['novos']} · atualizados {r['atualizados']} · "
        f"descartados {r['descartados']}. Os leads estão na aba **📋 Leads**."
    )
    if r.get("novos"):
        st.balloons()

abas = st.tabs(
    ["📊 Visão geral", "📋 Leads", "📌 Pipeline", "💬 Abordagem", "🔎 Buscar leads",
     "📥 Importar CSV", "📈 Relatórios", "⚙️ Configurações"]
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
        df = pd.DataFrame(rows)
        for col in ("tags",):
            if col not in df.columns:
                df[col] = ""
        df = df[
            ["id", "empresa", "telefone", "site", "cidade", "segmento", "score",
             "status", "tags", "oportunidade_motivo"]
        ]
        st.dataframe(
            df,
            width="stretch",
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "empresa": st.column_config.TextColumn("Empresa", width="medium"),
                "telefone": st.column_config.TextColumn("Telefone"),
                "site": st.column_config.LinkColumn("Site", display_text="abrir"),
                "cidade": st.column_config.TextColumn("Cidade"),
                "segmento": st.column_config.TextColumn("Segmento"),
                "score": st.column_config.ProgressColumn(
                    "Score", min_value=0, max_value=100, format="%d"
                ),
                "status": st.column_config.TextColumn("Status"),
                "tags": st.column_config.TextColumn("🏷️ Etiquetas"),
                "oportunidade_motivo": st.column_config.TextColumn(
                    "Oportunidade de abordagem", width="large"
                ),
            },
        )

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

        st.markdown("#### 🏷️ Etiquetas do lead")
        st.caption("Separe por vírgula. Ex.: quente, retornar, indicação")
        tags_novo = st.text_input("Etiquetas", lead.get("tags") or "", key=f"tags_{sel}")
        if st.button("Salvar etiquetas"):
            repository.atualizar_campos(engine, sel, {"tags": tags_novo.strip()})
            st.success("Etiquetas salvas.")
            st.rerun()
    else:
        st.info("Nenhum lead com esses filtros.")

# ------------------------------------------------------------------ Pipeline
with abas[2]:
    st.subheader("📌 Pipeline")
    st.caption(
        "Seu funil em colunas. Em cada card, escolha **mover →** para mandar o lead "
        "para outra etapa (salva na hora). Aprovados na Abordagem entram em *Contato "
        "Enviado* automaticamente."
    )
    leads_all = repository.listar_leads(engine)
    if not leads_all:
        st.info("Nenhum lead ainda. Use a aba **🔎 Buscar leads** para começar.")
    else:
        estagios = crm.PIPELINE  # etapas principais do funil (em colunas)
        colunas = st.columns(len(estagios))
        for coluna, etapa in zip(colunas, estagios):
            grupo = [l for l in leads_all if (l["status"] or "Novo Lead") == etapa]
            coluna.markdown(f"**{etapa}**")
            coluna.caption(f"{len(grupo)} lead(s)")
            for l in grupo:
                with coluna.container(border=True):
                    st.markdown(f"**{l['empresa']}**")
                    extra = f" · 🏷️ {l['tags']}" if l.get("tags") else ""
                    st.caption(f"⭐ {l['score']}{extra}")
                    destinos = [e for e in crm.TODOS_STATUS if e != etapa]
                    novo = st.selectbox(
                        "mover →", ["—"] + destinos,
                        key=f"mv_{l['id']}", label_visibility="collapsed",
                    )
                    if novo != "—":
                        repository.atualizar_campos(
                            engine, l["id"], {"status": novo, "ultima_acao": f"Movido para {novo}"}
                        )
                        st.rerun()

# ----------------------------------------------------------------- Abordagem
with abas[3]:
    st.subheader("💬 Abordagem — fila pronta pra enviar")
    st.caption(
        "O DemandOS escreve uma mensagem personalizada pra cada lead qualificado. "
        "Revise, ajuste se quiser e clique em **Abrir no WhatsApp** — a mensagem já "
        "vai digitada; você só aperta enviar. **Nada é enviado sozinho** (seu número fica seguro)."
    )

    cmsg = cfg.get("mensagem", {})
    leads_abordagem = [
        r for r in repository.listar_leads(engine, score_min=cfg["scoring"]["score_minimo"])
        if r["status"] in ("Novo Lead", "Qualificado")
        and (r["telefone"] or r["whatsapp"])
    ]

    if not leads_abordagem:
        st.info(
            "Nenhum lead na fila ainda. Use a aba **🔎 Buscar leads** pra encontrar empresas "
            "(só entram aqui leads com telefone e score acima do mínimo)."
        )
    else:
        st.write(f"**{len(leads_abordagem)}** leads prontos para abordagem:")
        for r in leads_abordagem[:25]:
            lead = dict(r)
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**{lead['empresa']}** · {lead.get('cidade','')} · score {lead['score']}")
                c1.caption(f"📞 {lead.get('telefone') or lead.get('whatsapp')} · {lead.get('oportunidade_motivo','')}")
                msg = st.text_area(
                    "Mensagem",
                    value=message_generator.gerar_mensagem(lead, {"mensagem": cmsg}),
                    key=f"msg_{lead['id']}",
                    height=140,
                    label_visibility="collapsed",
                )
                link = message_generator.link_whatsapp(lead, msg)
                b1, b2 = st.columns([1, 1])
                if link:
                    # target="zap" reaproveita SEMPRE a mesma aba do WhatsApp Web
                    # (não abre uma aba nova a cada lead).
                    b1.markdown(
                        f'<a href="{link}" target="zap" style="display:block;text-align:center;'
                        f"background:#25D366;color:#fff;padding:9px 0;border-radius:8px;"
                        f'font-weight:600;text-decoration:none">📱 Abrir conversa no WhatsApp</a>',
                        unsafe_allow_html=True,
                    )
                else:
                    b1.button("📱 Sem WhatsApp válido", disabled=True, key=f"nowa_{lead['id']}", use_container_width=True)
                if b2.button("✅ Marquei como enviado", key=f"sent_{lead['id']}", use_container_width=True):
                    crm.mover_status(engine, lead["id"], "Contato Enviado", "Abordagem via WhatsApp")
                    st.rerun()

# --------------------------------------------------------------- Buscar leads
with abas[4]:
    st.subheader("🔎 Buscar leads em tempo real")
    st.caption(
        "Escolha o segmento, a cidade e **quantos leads** quer; clique em **Buscar agora**. "
        "O DemandOS encontra empresas reais, analisa o site, pontua, deduplica e salva."
    )
    segmentos = cfg.get("segmentos", [])
    cidades_cfg = cfg.get("cidades", [])
    cidades = [f"{c['cidade']}/{c['estado']}" for c in cidades_cfg]
    fontes = ["OpenStreetMap (grátis)"]
    if config.tem_chave_google():
        fontes.append("Google Maps")

    cg0, cg1, cg2, cg3 = st.columns([1.5, 1.2, 1.2, 1.1])
    fonte = cg0.selectbox("Fonte", fontes)
    seg = cg1.selectbox("Segmento", segmentos or ["(defina em Configurações)"])
    cidade_sel = cg2.selectbox("Cidade", cidades or ["(defina em Configurações)"])
    limite = cg3.number_input("Quantos leads buscar", 1, 60, 15)

    _usa_google = fonte.startswith("Google")

    def _buscar(s, ci, uf, n):
        if _usa_google:
            return lead_finder.buscar_google_places(engine, s, ci, uf, n)
        return lead_finder.buscar_openstreetmap(engine, s, ci, uf, n)

    if st.button("🚀 Buscar agora", type="primary", disabled=not (segmentos and cidades)):
        cidade, estado = (cidade_sel.split("/") + [""])[:2]
        with st.spinner(f"Buscando '{seg}' em {cidade} e analisando os sites em tempo real..."):
            resumo = _buscar(seg, cidade, estado, int(limite))
        resumo["seg"] = seg
        resumo["cidade"] = cidade
        st.session_state["busca_result"] = resumo
        st.rerun()

    st.divider()
    st.markdown("##### ⚡ Busca em lote — varre todos os seus segmentos e cidades")
    st.caption("Diga quantos leads NOVOS você quer e o DemandOS vai buscando em tudo até alcançar.")
    alvo = st.number_input("Quantos leads novos trazer", 5, 100, 20, key="alvo_lote")
    if st.button("⚡ Buscar em lote", disabled=not (segmentos and cidades)):
        prog = st.progress(0.0, text="Iniciando...")
        total = {"encontrados": 0, "novos": 0, "atualizados": 0, "descartados": 0}
        combos = [(s, c) for c in cidades_cfg for s in segmentos]
        for s, c in combos:
            if total["novos"] >= alvo:
                break
            prog.progress(
                min(total["novos"] / alvo, 0.99),
                text=f"Buscando {s} em {c['cidade']}... ({total['novos']}/{alvo} novos)",
            )
            try:
                r = _buscar(s, c["cidade"], c["estado"], min(int(alvo), 12))
                for k in total:
                    total[k] += r.get(k, 0)
            except Exception as e:  # noqa: BLE001
                st.warning(f"Pulei {s} em {c['cidade']}: {e}")
        prog.progress(1.0, text="Concluído!")
        total["seg"] = "vários segmentos"
        total["cidade"] = "todas as suas cidades"
        st.session_state["busca_result"] = total
        st.rerun()

# -------------------------------------------------------------- Importar CSV
with abas[5]:
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
with abas[6]:
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
with abas[7]:
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

    st.markdown("##### ✍️ Mensagem de abordagem")
    cmsg = cfg.get("mensagem", {})
    m1, m2 = st.columns(2)
    remetente = m1.text_input("Seu nome (como você assina)", cmsg.get("remetente", ""))
    cargo = m2.text_input("Seu cargo/título", cmsg.get("cargo", "estrategista de marketing"))
    proposta = st.text_input("O que você oferece", cmsg.get("proposta", "atrair mais clientes pela internet"))

    if st.button("💾 Salvar configurações"):
        novo = dict(cfg)
        novo["captacao"]["leads_por_dia"] = int(leads_dia)
        novo["captacao"]["horario_inicial"] = h1
        novo["captacao"]["horario_final"] = h2
        novo["scoring"]["score_minimo"] = int(score_min)
        novo["mensagem"] = {"remetente": remetente, "cargo": cargo, "proposta": proposta}
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
