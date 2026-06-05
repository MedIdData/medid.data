-- Migration: Ajustar limites do plano Gratuito
-- Data: 2026-06-05
-- Descrição: Atualizar todos os usuários para novos limites do Gratuito (20/dia, 100/mês)
--            Administradores recebem limites ilimitados (0 = sem limite)

-- 1. Atualizar plano Gratuito
UPDATE planos
SET
    limite_diario = 20,
    limite_mensal = 100,
    descricao = 'Plano gratuito com limites básicos para testes e pequenos volumes'
WHERE nome = 'Gratuito';

-- 2. Criar plano Admin se não existir
INSERT INTO planos (nome, descricao, limite_diario, limite_mensal, valor_mensal_centavos, ativo, criado_em)
SELECT
    'Admin',
    'Plano exclusivo para administradores do sistema (uso interno ilimitado)',
    0,  -- Ilimitado
    0,  -- Ilimitado
    0,
    true,
    NOW()
WHERE NOT EXISTS (SELECT 1 FROM planos WHERE nome = 'Admin');

-- 3. Atualizar usuários ADMINISTRADORES para limites ilimitados
UPDATE usuarios
SET
    limite_diario = 0,
    limite_mensal = 0
WHERE perfil IN ('ADMINISTRADOR', 'ADMIN');

-- 4. Atualizar usuários NÃO-ADMIN que estão com limites antigos para novos limites do Gratuito
-- (50→20, 1000→100 ou qualquer limite que não seja de outro plano)
UPDATE usuarios
SET
    limite_diario = 20,
    limite_mensal = 100
WHERE perfil NOT IN ('ADMINISTRADOR', 'ADMIN')
  AND (
    -- Limites antigos do Gratuito
    (limite_diario = 50 AND limite_mensal = 1000)
    OR (limite_diario = 100 AND limite_mensal = 2000)
    OR (limite_diario IS NULL OR limite_mensal IS NULL)
    -- Não mexer em quem já tem planos pagos
    OR NOT (
        (limite_diario = 500 AND limite_mensal = 10000)   -- Básico
        OR (limite_diario = 2000 AND limite_mensal = 50000) -- Profissional
        OR (limite_diario = 0 AND limite_mensal = 0)       -- Enterprise
    )
  );

-- Log
DO $$
BEGIN
    RAISE NOTICE 'Migration 008: Limites ajustados - Gratuito: 20/100, Admin: ∞';
END $$;
