-- Migração: Adiciona extensões PostgreSQL necessárias
-- Data: 2026-06-04
-- Descrição: Cria pg_trgm e unaccent para busca fuzzy de medicamentos

-- Extensão pg_trgm: Trigram similarity para fuzzy matching
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Extensão unaccent: Remove acentos para busca normalizada
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Verificação
SELECT extname, extversion
FROM pg_extension
WHERE extname IN ('pg_trgm', 'unaccent')
ORDER BY extname;
