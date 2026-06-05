-- Migration 007: Sistema de convites para ativação de conta
-- Data: 2026-06-05
-- Descrição: Permite que admins criem usuários sem definir senha,
--            gerando link de convite para o usuário definir sua própria senha

-- Criar tabela de convites
CREATE TABLE IF NOT EXISTS convites_usuario (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    token VARCHAR(64) UNIQUE NOT NULL,
    usado BOOLEAN DEFAULT FALSE,
    expira_em TIMESTAMP NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usado_em TIMESTAMP
);

-- Criar índices
CREATE INDEX IF NOT EXISTS idx_convites_token ON convites_usuario(token);
CREATE INDEX IF NOT EXISTS idx_convites_usuario ON convites_usuario(usuario_id);
CREATE INDEX IF NOT EXISTS idx_convites_usado ON convites_usuario(usado, expira_em);

-- Comentários
COMMENT ON TABLE convites_usuario IS 'Convites para usuários definirem senha no primeiro acesso';
COMMENT ON COLUMN convites_usuario.token IS 'Token único de ativação (urlsafe)';
COMMENT ON COLUMN convites_usuario.usado IS 'Se o convite já foi utilizado';
COMMENT ON COLUMN convites_usuario.expira_em IS 'Data/hora de expiração (padrão: 72h após criação)';
COMMENT ON COLUMN convites_usuario.usado_em IS 'Quando o convite foi usado';
