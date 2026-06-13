# Colocar o SDR IA no ar (online, com login)

Guia passo a passo para publicar o painel num link `https://...` acessível de
qualquer lugar, **de graça**, no **Streamlit Community Cloud**, com **login** e
**banco de leads que nunca some** (Postgres grátis).

São 3 contas gratuitas (eu não consigo criar por você — exigem seu cadastro):
**GitHub** (guardar o código), **Supabase** (banco de leads), **Streamlit Cloud** (hospedar).

Tempo estimado: ~30–40 min na primeira vez. Faça na ordem.

---

## Visão geral

```
Seu PC (código)  ──push──>  GitHub  ──conecta──>  Streamlit Cloud  ──lê──>  Supabase (Postgres)
                                                        │
                                                   link https://... com login
```

---

## Parte 1 — Banco de leads grátis (Supabase)

1. Acesse https://supabase.com e crie uma conta grátis (pode entrar com o GitHub).
2. Clique em **New project**. Dê um nome (ex.: `sdr-ia`), defina uma **senha do banco**
   (anote!) e escolha a região **South America (São Paulo)**.
3. Espere o projeto criar (~2 min).
4. Vá em **Project Settings → Database → Connection string → URI**.
5. Copie a string. Ela se parece com:
   ```
   postgresql://postgres:[SUA-SENHA]@db.xxxxx.supabase.co:5432/postgres
   ```
6. Troque `[SUA-SENHA]` pela senha que você definiu e **acrescente `?sslmode=require` no final**:
   ```
   postgresql://postgres:suasenha@db.xxxxx.supabase.co:5432/postgres?sslmode=require
   ```
   Guarde isso — é o seu **DATABASE_URL**.

---

## Parte 2 — Código no GitHub

1. Acesse https://github.com e crie uma conta grátis.
2. Crie um repositório: botão **New** → nome `sdr-ia` → marque **Private**
   (privado, só você vê) → **Create repository**.
3. Agora suba a pasta do projeto. O jeito mais simples sem instalar nada:
   - Na página do repositório, clique em **uploading an existing file**.
   - Abra a pasta `C:\Users\Guilherme\sdr-ia` e **arraste todos os arquivos** para o navegador.
   - ⚠️ **NÃO** suba estes (eles têm segredos ou são locais): `.env`, `auth_config.yaml`,
     e as pastas `data/`, `logs/`, `reports/`. (O arquivo `.gitignore` já evita isso se
     você usar o Git pelo terminal; no upload manual, simplesmente não os arraste.)
   - Clique em **Commit changes**.

> 💡 Se preferir, posso te guiar a instalar o GitHub Desktop (clica-clica) numa próxima conversa.

---

## Parte 3 — Gerar seu login

No seu PC, dê duplo clique em **`configurar-login.bat`** (ou rode `python tools/set_password.py`).
- Digite o usuário e a senha que você quer usar para entrar no painel.
- O programa vai **imprimir um bloco de texto** (começa com `[auth.credentials...`).
- **Copie esse bloco inteiro** — você vai colar no Streamlit Cloud no próximo passo.

---

## Parte 4 — Publicar no Streamlit Cloud

1. Acesse https://share.streamlit.io e entre **com sua conta do GitHub**.
2. Clique em **New app** → **Deploy a public app from a repo** (ou "from existing repo").
3. Preencha:
   - **Repository:** `seu-usuario/sdr-ia`
   - **Branch:** `main`
   - **Main file path:** `dashboard/app.py`
4. Clique em **Advanced settings → Secrets** e cole o seguinte (ajustando os valores):
   ```toml
   DATABASE_URL = "postgresql://postgres:suasenha@db.xxxxx.supabase.co:5432/postgres?sslmode=require"
   GOOGLE_PLACES_API_KEY = "sua_chave_do_google_ou_deixe_vazio"

   # >>> cole aqui o bloco que o configurar-login.bat imprimiu <<<
   [auth.credentials.usernames.SEU_USUARIO]
   name = "Seu Nome"
   password = "$2b$12$....hash...."
   email = ""

   [auth.cookie]
   name = "sdr_ia_auth"
   key = "a_chave_aleatoria_que_foi_impressa"
   expiry_days = 30
   ```
5. Clique em **Deploy**. Espere alguns minutos.
6. Pronto! Você recebe um link `https://sdr-ia-....streamlit.app`. Abra → aparece a
   **tela de login** → entre com seu usuário e senha. 🎉

> Salve o link nos favoritos do celular e do PC. Seus leads ficam guardados no Supabase,
> então nunca somem, mesmo que o app reinicie.

---

## Dúvidas comuns

| Pergunta | Resposta |
|---|---|
| O app "dormiu"? | No plano grátis, ele hiberna sem uso. Abrir o link acorda em ~30s. |
| Mudei o config.yaml online e não salvou | Na nuvem o arquivo é só-leitura. Edite o `config.yaml` no GitHub (ele recarrega sozinho). |
| Quero trocar a senha | Rode `configurar-login.bat` de novo e atualize o bloco em Secrets do Streamlit. |
| Esqueci de adicionar a chave do Google | Adicione a linha `GOOGLE_PLACES_API_KEY` em Secrets a qualquer momento. |
| É seguro? | O login protege o acesso; o repositório é privado; os segredos ficam só no Streamlit (não no código). |

---

## Rodar local continua funcionando

No seu PC: `configurar-login.bat` (uma vez) → `run-dashboard.bat`.
Sem `DATABASE_URL`, ele usa o banco local (SQLite). Com a nuvem configurada, os dois
podem coexistir (local usa SQLite; online usa Postgres).
