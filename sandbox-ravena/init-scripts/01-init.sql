-- ============================================
-- SCRIPT DE INICIALIZAÇÃO - SANDBOX RAVENA
-- Ambiente isolado para testes de segurança
-- ============================================

-- Criar extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- TABELAS DE TESTE (Dados Fictícios)
-- ============================================

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    balance DECIMAL(15,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'active',
    role VARCHAR(20) DEFAULT 'user', -- 'user' ou 'admin'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de transações (saques e depósitos)
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    type VARCHAR(20) NOT NULL, -- 'deposit', 'withdrawal', 'bet', 'win'
    amount DECIMAL(15,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'completed'
    payment_method VARCHAR(50),
    pix_key VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de apostas em slots
CREATE TABLE IF NOT EXISTS slot_bets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    game_id VARCHAR(50) NOT NULL,
    bet_amount DECIMAL(15,2) NOT NULL,
    win_amount DECIMAL(15,2) DEFAULT 0.00,
    result JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de sessões
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    token VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABELAS DE AUDITORIA (Logs)
-- ============================================

-- Log de todas as operações
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100),
    operation VARCHAR(10), -- 'INSERT', 'UPDATE', 'DELETE'
    old_data JSONB,
    new_data JSONB,
    user_id UUID,
    ip_address INET,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Log de tentativas de ataque
CREATE TABLE IF NOT EXISTS attack_log (
    id BIGSERIAL PRIMARY KEY,
    attack_type VARCHAR(50), -- 'sql_injection', 'brute_force', 'session_hijack', 'idor'
    endpoint VARCHAR(255),
    payload TEXT,
    blocked BOOLEAN DEFAULT FALSE,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TRIGGERS DE AUDITORIA
-- ============================================

-- Função para registrar operações
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (table_name, operation, old_data, new_data, user_id, ip_address)
    VALUES (
        TG_TABLE_NAME,
        TG_OP,
        CASE WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN to_jsonb(NEW) ELSE NULL END,
        CASE 
            WHEN TG_OP = 'DELETE' THEN OLD.id
            ELSE NEW.id
        END,
        inet_client_addr()
    );
    
    -- Log especial para operações financeiras
    IF TG_TABLE_NAME IN ('users', 'transactions') THEN
        INSERT INTO audit_log (table_name, operation, new_data, ip_address)
        VALUES (
            'FINANCIAL_ALERT',
            TG_OP,
            jsonb_build_object(
                'table', TG_TABLE_NAME,
                'operation', TG_OP,
                'amount', CASE WHEN TG_OP = 'DELETE' THEN NULL ELSE NEW.balance END
            ),
            inet_client_addr()
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar triggers em tabelas sensíveis
CREATE TRIGGER audit_users
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER audit_transactions
    AFTER INSERT OR UPDATE OR DELETE ON transactions
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER audit_slot_bets
    AFTER INSERT OR UPDATE OR DELETE ON slot_bets
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- ============================================
-- FUNÇÕES DE VALIDAÇÃO DE SEGURANÇA
-- ============================================

-- Função para validar saque (proteção contra SQL Injection)
CREATE OR REPLACE FUNCTION validate_withdrawal(
    p_user_id UUID,
    p_amount DECIMAL,
    p_pix_key VARCHAR
) RETURNS TABLE(success BOOLEAN, message TEXT) AS $$
DECLARE
    v_balance DECIMAL;
    v_user_status VARCHAR;
BEGIN
    -- Verificar se o usuário existe e está ativo
    SELECT balance, status INTO v_balance, v_user_status
    FROM users WHERE id = p_user_id;
    
    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'Usuário não encontrado'::TEXT;
        RETURN;
    END IF;
    
    IF v_user_status != 'active' THEN
        RETURN QUERY SELECT FALSE, 'Conta inativa'::TEXT;
        RETURN;
    END IF;
    
    -- Verificar saldo
    IF v_balance < p_amount THEN
        RETURN QUERY SELECT FALSE, 'Saldo insuficiente'::TEXT;
        RETURN;
    END IF;
    
    -- Verificar valor mínimo e máximo
    IF p_amount < 10 THEN
        RETURN QUERY SELECT FALSE, 'Valor mínimo: R$ 10,00'::TEXT;
        RETURN;
    END IF;
    
    IF p_amount > 5000 THEN
        RETURN QUERY SELECT FALSE, 'Valor máximo: R$ 5.000,00'::TEXT;
        RETURN;
    END IF;
    
    -- Verificar PIX key
    IF p_pix_key IS NULL OR LENGTH(p_pix_key) < 10 THEN
        RETURN QUERY SELECT FALSE, 'Chave PIX inválida'::TEXT;
        RETURN;
    END IF;
    
    -- Tudo OK
    RETURN QUERY SELECT TRUE, 'Saque autorizado'::TEXT;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- DADOS FICTÍCIOS DE TESTE
-- ============================================

-- Inserir usuários de teste
INSERT INTO users (username, email, password_hash, balance, status, role) VALUES
    ('attacker_001', 'attacker@sandbox.test', crypt('test123', gen_salt('bf')), 10000.00, 'active', 'user'),
    ('vitima_001', 'vitima1@sandbox.test', crypt('test123', gen_salt('bf')), 5000.00, 'active', 'user'),
    ('vitima_002', 'vitima2@sandbox.test', crypt('test123', gen_salt('bf')), 3464.00, 'active', 'user'),
    ('lara_001', 'lara1@sandbox.test', crypt('test123', gen_salt('bf')), 0.00, 'active', 'user'),
    ('admin_test', 'admin@sandbox.test', crypt('admin123', gen_salt('bf')), 0.00, 'active', 'admin');

-- Inserir transações de teste
INSERT INTO transactions (user_id, type, amount, status, payment_method, pix_key) 
SELECT id, 'deposit', 10000.00, 'completed', 'pix', 'attacker@pix.test'
FROM users WHERE username = 'attacker_001';

-- ============================================
-- VIEWS PARA MONITORAMENTO
-- ============================================

-- View de tentativas de ataque
CREATE VIEW v_attack_attempts AS
SELECT 
    attack_type,
    COUNT(*) as total,
    SUM(CASE WHEN blocked THEN 1 ELSE 0 END) as blocked_count,
    SUM(CASE WHEN NOT blocked THEN 1 ELSE 0 END) as success_count,
    MAX(timestamp) as last_attempt
FROM attack_log
GROUP BY attack_type;

-- View de transações suspeitas
CREATE VIEW v_suspicious_transactions AS
SELECT 
    t.id,
    u.username,
    t.type,
    t.amount,
    t.status,
    t.pix_key,
    t.created_at,
    CASE 
        WHEN t.amount > 1000 THEN 'ALTO_VALOR'
        WHEN t.pix_key LIKE '%attacker%' THEN 'PIX_SUSPEITO'
        ELSE 'NORMAL'
    END as risk_level
FROM transactions t
JOIN users u ON t.user_id = u.id
WHERE t.created_at > NOW() - INTERVAL '1 hour';

-- View de sessões ativas
CREATE VIEW v_active_sessions AS
SELECT 
    s.id,
    u.username,
    s.ip_address,
    s.user_agent,
    s.created_at,
    s.expires_at,
    CASE 
        WHEN s.expires_at < NOW() THEN 'EXPIRADA'
        ELSE 'ATIVA'
    END as status
FROM sessions s
JOIN users u ON s.user_id = u.id
WHERE s.expires_at > NOW() - INTERVAL '24 hours';

-- ============================================
--ÍNDICES PARA PERFORMANCE
-- ============================================

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_slot_bets_user_id ON slot_bets(user_id);
CREATE INDEX idx_sessions_token ON sessions(token);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX idx_attack_log_timestamp ON attack_log(timestamp);

-- ============================================
-- PERMISSÕES (Segurança)
-- ============================================

-- Criar role de aplicação
CREATE ROLE ravena_app_role;

-- Conceder permissões necessárias
GRANT SELECT, INSERT, UPDATE ON users TO ravena_app_role;
GRANT SELECT, INSERT, UPDATE ON transactions TO ravena_app_role;
GRANT SELECT, INSERT, UPDATE ON slot_bets TO ravena_app_role;
GRANT SELECT, INSERT ON sessions TO ravena_app_role;
GRANT SELECT, INSERT ON attack_log TO ravena_app_role;

-- Negar acesso direto a tabelas de auditoria (apenas via funções)
REVOKE ALL ON audit_log FROM ravena_app_role;
REVOKE ALL ON v_attack_attempts FROM ravena_app_role;
REVOKE ALL ON v_suspicious_transactions FROM ravena_app_role;
