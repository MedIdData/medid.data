-- Migration: Remover sistema de planos e assinaturas
-- Data: 2026-06-05
-- Descrição: Simplificar para gestão direta de limites por usuário

-- 1. Garantir que todos os usuários tenham limites definidos
UPDATE usuarios
SET
    limite_diario = COALESCE(limite_diario, 20),
    limite_mensal = COALESCE(limite_mensal, 100)
WHERE perfil NOT IN ('ADMINISTRADOR', 'ADMIN')
  AND (limite_diario IS NULL OR limite_mensal IS NULL);

-- 2. Garantir que administradores tenham limites ilimitados
UPDATE usuarios
SET
    limite_diario = 0,
    limite_mensal = 0
WHERE perfil IN ('ADMINISTRADOR', 'ADMIN');

-- 3. Remover tabela de planos (não mais necessária)
-- Não vamos dropar ainda, apenas desativar todos
UPDATE planos SET ativo = false;

-- 4. Adicionar constraint para garantir limites sempre definidos
ALTER TABLE usuarios
ALTER COLUMN limite_diario SET NOT NULL,
ALTER COLUMN limite_diario SET DEFAULT 20;

ALTER TABLE usuarios
ALTER COLUMN limite_mensal SET NOT NULL,
ALTER COLUMN limite_mensal SET DEFAULT 100;

-- Log
DO $$
BEGIN
    RAISE NOTICE 'Migration 010: Sistema de planos removido - gestão direta por limites';
END $$;
