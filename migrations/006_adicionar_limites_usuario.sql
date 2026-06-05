-- Migration 006: Adicionar limites individuais por usuário
-- Data: 2026-06-05
-- Descrição: Adiciona colunas limite_diario e limite_mensal na tabela usuarios
--            NULL = ilimitado (para ADMINISTRADOR) ou herda do plano
--            Integer = limite personalizado por usuário

-- Adicionar colunas de limite
ALTER TABLE usuarios
ADD COLUMN IF NOT EXISTS limite_diario INTEGER,
ADD COLUMN IF NOT EXISTS limite_mensal INTEGER;

-- Comentários
COMMENT ON COLUMN usuarios.limite_diario IS 'Limite diário de requisições (NULL = ilimitado ou usa plano)';
COMMENT ON COLUMN usuarios.limite_mensal IS 'Limite mensal de requisições (NULL = ilimitado ou usa plano)';

-- Definir limites padrão para usuários não-admin existentes
UPDATE usuarios
SET
    limite_diario = 100,
    limite_mensal = 2000
WHERE perfil != 'ADMINISTRADOR'
  AND limite_diario IS NULL;

-- Garantir que administradores fiquem NULL (ilimitados)
UPDATE usuarios
SET
    limite_diario = NULL,
    limite_mensal = NULL
WHERE perfil = 'ADMINISTRADOR';
