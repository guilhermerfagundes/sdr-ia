# Guia de Instalação — SDR IA

Feito para quem **não é técnico**. Siga na ordem. Leva ~15 minutos na primeira vez.

---

## ✅ O que este sistema faz (Fase 1)

- Encontra empresas no **Google Maps** (ou importa sua planilha CSV).
- **Analisa o site** de cada uma (SEO, pixel, anúncios, velocidade).
- Dá uma **nota de 0 a 100** com justificativa e o **motivo de abordagem**.
- Evita **leads duplicados** automaticamente.
- Organiza tudo num **CRM** (pipeline) e gera **relatório diário**.
- Mostra tudo num **painel visual** que abre no navegador.

> Envio de WhatsApp, follow-ups automáticos e agenda entram nas próximas fases.

---

## Passo 1 — Instalar o Python (uma vez só)

> Se você pediu para o assistente instalar, isso **já está feito** — pule para o Passo 2.

1. Acesse https://www.python.org/downloads/
2. Baixe o Python 3.12 (botão amarelo "Download Python").
3. Ao abrir o instalador, **MARQUE a caixa "Add Python to PATH"** (muito importante!).
4. Clique em "Install Now" e aguarde.

---

## Passo 2 — Instalar o sistema

Na pasta `sdr-ia`, dê **duplo clique** em **`install.bat`**.
Uma janela preta vai abrir, instalar tudo e dizer "Pronto!". Pode fechar.

---

## Passo 3 — Criar seu login (uma vez)

Dê **duplo clique** em **`configurar-login.bat`**.
Digite o **usuário** e a **senha** que você quer usar para entrar no painel.
(Isso também imprime um bloco de texto que você só vai usar se for colocar online — ver DEPLOY.md.)

---

## Passo 4 — Abrir o painel

Dê **duplo clique** em **`run-dashboard.bat`**.
- Uma janela preta abre (deixe ela aberta enquanto usar o sistema).
- O painel abre sozinho no seu navegador. Se não abrir, acesse: http://localhost:8501

- O painel abre com uma **tela de login** — entre com o usuário/senha do Passo 3.

🎉 Pronto! Você já pode **Importar CSV** e usar tudo.
Para testar agora, importe o arquivo de exemplo em `exports/exemplo_leads.csv`.

> 🌐 **Quer acessar de qualquer lugar (celular, outro PC)?** Veja o **DEPLOY.md** —
> passo a passo para publicar online, de graça, com login.

---

## Passo 5 (opcional) — Ativar a busca no Google Maps

A busca automática no Google Maps usa a **API oficial do Google** (paga, mas barata —
o Google ainda dá um crédito mensal gratuito que costuma cobrir bastante coisa).
**Sem isso o sistema funciona normalmente via importação de CSV.**

### Como obter a chave:

1. Acesse https://console.cloud.google.com/ e faça login com sua conta Google.
2. Crie um projeto (botão no topo → "Novo projeto"). Dê um nome qualquer.
3. No menu de busca, procure **"Places API"** e clique em **Ativar**.
4. Vá em **APIs e serviços → Credenciais → Criar credenciais → Chave de API**.
5. Copie a chave gerada (uma sequência de letras e números).
6. O Google vai pedir para **ativar o faturamento** (cadastrar um cartão). É obrigatório
   para a API funcionar, mas há crédito gratuito mensal.

### Como colocar a chave no sistema:

1. Na pasta `sdr-ia`, encontre o arquivo **`.env.example`**.
2. Faça uma cópia dele e renomeie a cópia para **`.env`** (só isso, sem nome antes do ponto).
3. Abra o `.env` no Bloco de Notas e cole a chave depois do `=`:
   ```
   GOOGLE_PLACES_API_KEY=cole_sua_chave_aqui
   ```
4. Salve. Feche e abra o painel de novo (`run-dashboard.bat`).
5. A aba **"Buscar leads"** vai estar liberada.

> 💡 Dica de segurança: no console do Google, restrinja a chave à "Places API" para evitar
> uso indevido caso ela vaze.

---

## Problemas comuns

| Sintoma | Solução |
|---|---|
| "Python não encontrado" | Reinstale o Python marcando "Add Python to PATH". |
| O painel não abre no navegador | Acesse manualmente http://localhost:8501 |
| Fechei a janela preta e o painel parou | Normal — abra `run-dashboard.bat` de novo. |
| Aba "Buscar leads" bloqueada | Falta configurar o `.env` com a chave (Passo 4). |

Para o dia a dia, veja o **GUIA-USO.md**.
