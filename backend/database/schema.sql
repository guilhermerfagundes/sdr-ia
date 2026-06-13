-- ============================================================
--  Esquema do banco (SQLite). Desenhado para migrar a
--  PostgreSQL no futuro sem mudar a lógica da aplicação.
-- ============================================================

CREATE TABLE IF NOT EXISTS leads (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    data_captura          TEXT,
    empresa               TEXT,
    responsavel           TEXT,
    telefone              TEXT,
    telefone_norm         TEXT,   -- só dígitos, para deduplicação
    whatsapp              TEXT,
    instagram             TEXT,
    instagram_norm        TEXT,   -- handle minúsculo, para deduplicação
    email                 TEXT,
    site                  TEXT,
    dominio               TEXT,   -- domínio do site, para deduplicação
    cidade                TEXT,
    estado                TEXT,
    segmento              TEXT,
    origem                TEXT,
    score                 INTEGER DEFAULT 0,
    score_justificativa   TEXT,
    oportunidade_motivo   TEXT,
    status                TEXT DEFAULT 'Novo Lead',
    ultima_acao           TEXT,
    proxima_acao          TEXT,
    dados_enriquecimento  TEXT,   -- JSON com os sinais coletados do site
    created_at            TEXT,
    updated_at            TEXT
);

CREATE INDEX IF NOT EXISTS idx_leads_telefone  ON leads (telefone_norm);
CREATE INDEX IF NOT EXISTS idx_leads_dominio   ON leads (dominio);
CREATE INDEX IF NOT EXISTS idx_leads_instagram ON leads (instagram_norm);
CREATE INDEX IF NOT EXISTS idx_leads_empresa   ON leads (empresa, cidade);
CREATE INDEX IF NOT EXISTS idx_leads_status    ON leads (status);

-- Log de eventos: captação, enriquecimento, erros, mudanças de status, etc.
CREATE TABLE IF NOT EXISTS eventos_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    momento     TEXT,
    tipo        TEXT,    -- captacao | enriquecimento | crm | erro | sistema
    lead_id     INTEGER,
    mensagem    TEXT,
    detalhe     TEXT
);

CREATE INDEX IF NOT EXISTS idx_log_momento ON eventos_log (momento);
CREATE INDEX IF NOT EXISTS idx_log_tipo    ON eventos_log (tipo);

-- Histórico de execuções de captação
CREATE TABLE IF NOT EXISTS config_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    momento         TEXT,
    segmento        TEXT,
    cidade          TEXT,
    estado          TEXT,
    encontrados     INTEGER,
    novos           INTEGER,
    atualizados     INTEGER,
    descartados     INTEGER
);
