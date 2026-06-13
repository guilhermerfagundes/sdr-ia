# Guia de Uso — SDR IA

Como operar o sistema no dia a dia. (Para instalar, veja **GUIA-INSTALACAO.md**.)

---

## Abrir o painel

Duplo clique em **`run-dashboard.bat`** → o painel abre no navegador.
A janela preta precisa ficar aberta enquanto você usa.

---

## As abas do painel

### 📊 Visão geral
Os números do seu funil: total de leads, encontrados hoje, qualificados, reuniões,
propostas, fechamentos, e gráficos por status e por segmento.

### 📋 Leads
A lista completa. Você pode **filtrar** por status, segmento e nota (score).
Embaixo, escolha um lead e **mova ele no pipeline** (ex.: de "Novo Lead" para
"Qualificado", "Contato Enviado", etc.).

### 🔎 Buscar leads (precisa da chave do Google — ver instalação)
Escolha um segmento e uma cidade (configurados na aba Configurações) e clique
**Buscar agora**. O sistema busca no Google Maps, analisa os sites, pontua e salva —
**pulando duplicados** automaticamente.

### 📥 Importar CSV
Suba uma planilha que você já tem. O sistema reconhece sozinho colunas como
*empresa, telefone, whatsapp, instagram, email, site, cidade, estado, segmento*.
A única obrigatória é **empresa** (ou "nome").
- Deixe **"Analisar o site"** marcado para o sistema visitar cada site e dar a nota
  completa (mais lento). Desmarque para uma importação rápida (sem nota de site).
- Teste com `exports/exemplo_leads.csv`.

### 📈 Relatórios
Clique em **Gerar relatório de hoje**. O relatório fica salvo na pasta `reports/`
e também aparece na tela. Bom para acompanhar a evolução diária.

### ⚙️ Configurações
Edite tudo pela tela (salva no `config.yaml`):
- **Leads por dia**, horários de trabalho.
- **Score mínimo**: abaixo disso o lead é considerado fraco.
- **Segmentos** e **Cidades** que você quer prospectar.
- **Exclusões**: palavras que descartam um lead (ex.: "agência de marketing",
  para não prospectar concorrentes).

---

## Como o sistema pontua os leads (0 a 100)

A lógica favorece quem **tem movimento mas tem marketing mal feito** (mais a vender):

- **+** tem contato (telefone/email) e tem Instagram.
- **+** tem site fraco (sem SEO, sem pixel, sem anúncios, lento).
- **+** tem Instagram mas não tem site (oportunidade clara).
- Faixas: **80+** quente · **50–79** morno · **40–49** frio · **<40** não prospectar.

Cada lead guarda a **justificativa da nota** e o **motivo de abordagem** (a "deixa"
para iniciar a conversa). Você vê isso na aba Leads.

---

## O pipeline (CRM)

```
Novo Lead → Qualificado → Contato Enviado → Follow-up 1 → Follow-up 2 →
Respondeu → Reunião Agendada → Reunião Realizada → Proposta → Fechado
```
Qualquer lead também pode ir para **Perdido** (e ser reaberto depois).

---

## Onde ficam os arquivos

| Pasta | O que tem |
|---|---|
| `data/sdr.db` | O banco de dados (todos os leads). **Faça backup deste arquivo.** |
| `reports/` | Relatórios diários gerados. |
| `logs/sdr.log` | Registro de tudo que o sistema fez (útil se algo der errado). |
| `exports/` | Planilhas (inclui o CSV de exemplo). |

> 💾 **Backup:** copie o arquivo `data/sdr.db` de vez em quando para um pen drive
> ou nuvem. É nele que estão todos os seus leads.

---

## Próximas fases (ainda não incluídas)

- **Fase 2:** gerar e **enviar mensagens** por WhatsApp (API oficial) + follow-ups automáticos.
- **Fase 3:** detectar respostas, **agendar reuniões**, Google Agenda, avisar você no WhatsApp.

Quando quiser avançar, é só pedir.
