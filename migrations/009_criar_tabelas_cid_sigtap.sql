-- Migration: Criar tabelas para CID-10 e SIGTAP
-- Data: 2026-06-05
-- Descrição: Tabelas adicionais para análise de risco completa

-- 1. CID-10 (Classificação Internacional de Doenças)
CREATE TABLE IF NOT EXISTS cid10 (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(10) NOT NULL UNIQUE,
    descricao TEXT NOT NULL,
    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cid10_codigo ON cid10(codigo);
CREATE INDEX IF NOT EXISTS idx_cid10_busca ON cid10 USING gin(to_tsvector('portuguese', descricao));

-- 2. SIGTAP Procedimentos
CREATE TABLE IF NOT EXISTS sigtap_procedimento (
    id SERIAL PRIMARY KEY,
    co_procedimento VARCHAR(20) NOT NULL UNIQUE,
    no_procedimento TEXT,
    tp_complexidade VARCHAR(2),
    tp_sexo VARCHAR(1),
    qt_maxima_execucao INTEGER,
    vl_idade_minima INTEGER,
    vl_idade_maxima INTEGER,
    vl_sh DECIMAL(10,2),
    vl_sa DECIMAL(10,2),
    vl_sp DECIMAL(10,2),
    co_financiamento VARCHAR(10),
    co_rubrica VARCHAR(10),
    qt_tempo_permanencia INTEGER,
    dt_competencia VARCHAR(6),
    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sigtap_proc_codigo ON sigtap_procedimento(co_procedimento);
CREATE INDEX IF NOT EXISTS idx_sigtap_proc_busca ON sigtap_procedimento USING gin(to_tsvector('portuguese', no_procedimento));

-- 3. SIGTAP Procedimento x CID (relação N:N)
CREATE TABLE IF NOT EXISTS sigtap_procedimento_cid (
    id SERIAL PRIMARY KEY,
    co_procedimento VARCHAR(20) NOT NULL,
    co_cid VARCHAR(10) NOT NULL,
    st_principal VARCHAR(1),
    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sigtap_cid_procedimento ON sigtap_procedimento_cid(co_procedimento);
CREATE INDEX IF NOT EXISTS idx_sigtap_cid_cid ON sigtap_procedimento_cid(co_cid);
CREATE INDEX IF NOT EXISTS idx_sigtap_cid_composto ON sigtap_procedimento_cid(co_procedimento, co_cid);

-- Log
DO $$
BEGIN
    RAISE NOTICE 'Migration 009: Tabelas CID-10 e SIGTAP criadas com sucesso';
END $$;
