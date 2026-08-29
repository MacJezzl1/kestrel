-- ====================================================================
-- KESTREL QUANTUM TRADING INTELLIGENCE — COMPLETE SUPABASE DATABASE
-- CapeChain Labs — "See every market. Miss nothing."
-- Project URL: https://fuzhwfvixsiyjwokigkp.supabase.co
-- ====================================================================

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. DROP EXISTING TABLES IN REVERSE DEPENDENCY ORDER (CLEAN SLATE RESET)
DROP TABLE IF EXISTS performance_snapshots CASCADE;
DROP TABLE IF EXISTS system_logs CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS client_subscriptions CASCADE;
DROP TABLE IF EXISTS trades CASCADE;
DROP TABLE IF EXISTS signals CASCADE;
DROP TABLE IF EXISTS ai_models CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS licenses CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ====================================================================
-- TABLE 1: USERS & AUTHENTICATION
-- ====================================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    license_tier VARCHAR(32) DEFAULT 'PRO', -- 'PRO', 'ENTERPRISE', 'LIFETIME'
    license_status VARCHAR(32) DEFAULT 'ACTIVE',
    token_version INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================================================================
-- TABLE 2: LICENSES & USAGE LIMITS
-- ====================================================================
CREATE TABLE licenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    license_key VARCHAR(128) UNIQUE NOT NULL,
    tier VARCHAR(32) DEFAULT 'PRO',
    status VARCHAR(32) DEFAULT 'ACTIVE',
    signals_used_today INT DEFAULT 0,
    signals_limit INT DEFAULT 100,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================================================================
-- TABLE 3: ACCOUNTS (MT5 BROKER CONNECTIONS & PAMM SWARM)
-- ====================================================================
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    account_number VARCHAR(64) UNIQUE NOT NULL,
    broker_name VARCHAR(128) DEFAULT 'Deriv.com Limited',
    server VARCHAR(128) DEFAULT 'Deriv-Demo',
    license_key VARCHAR(128) NOT NULL,
    license_tier VARCHAR(32) DEFAULT 'PRO_CLIENT', -- 'ENTERPRISE_MASTER', 'ENTERPRISE_CLIENT', 'PRO_CLIENT'
    balance NUMERIC(15, 2) DEFAULT 0.00,
    equity NUMERIC(15, 2) DEFAULT 0.00,
    currency VARCHAR(8) DEFAULT 'USD',
    initial_balance NUMERIC(15, 2) DEFAULT 0.00,
    total_profit NUMERIC(15, 2) DEFAULT 0.00,
    today_profit NUMERIC(15, 2) DEFAULT 0.00,
    max_drawdown_pct NUMERIC(6, 2) DEFAULT 0.00,
    current_drawdown_pct NUMERIC(6, 2) DEFAULT 0.00,
    recovery_level VARCHAR(32) DEFAULT 'OPTIMAL', -- 'OPTIMAL', 'CAUTION', 'RECOVERY_SHIELD'
    recovery_multiplier NUMERIC(4, 2) DEFAULT 1.00,
    auto_trade_enabled BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    last_heartbeat TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================================================================
-- TABLE 4: TRADES (REAL-TIME EXECUTION JOURNAL & MT5 DEALS)
-- ====================================================================
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    account_number VARCHAR(64),
    mt5_ticket BIGINT,
    deal_id VARCHAR(64),
    instrument VARCHAR(64) NOT NULL,
    timeframe VARCHAR(16) DEFAULT 'H1',
    direction VARCHAR(8) NOT NULL, -- 'BUY', 'SELL'
    lot_size NUMERIC(8, 2) NOT NULL DEFAULT 0.01,
    entry_price NUMERIC(15, 5) NOT NULL,
    exit_price NUMERIC(15, 5),
    stop_loss NUMERIC(15, 5),
    take_profit NUMERIC(15, 5),
    pnl NUMERIC(15, 2) DEFAULT 0.00,
    profit_amount NUMERIC(15, 2) DEFAULT 0.00,
    pnl_pips NUMERIC(10, 2) DEFAULT 0.00,
    confidence_at_entry NUMERIC(5, 4),
    swarm_consensus_pct NUMERIC(5, 2),
    market_regime VARCHAR(64),
    magic_number BIGINT DEFAULT 120999,
    status VARCHAR(32) DEFAULT 'open', -- 'open', 'closed', 'cancelled'
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ====================================================================
-- TABLE 5: SIGNALS (120-AI QUANTUM SWARM HIGH-CONVICTION FEED)
-- ====================================================================
CREATE TABLE signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instrument VARCHAR(64) NOT NULL,
    timeframe VARCHAR(16) NOT NULL,
    direction VARCHAR(8) NOT NULL, -- 'BUY', 'SELL'
    confidence NUMERIC(5, 4) NOT NULL,
    regime VARCHAR(64) NOT NULL,
    buy_votes INT DEFAULT 0,
    sell_votes INT DEFAULT 0,
    hold_votes INT DEFAULT 0,
    total_models INT DEFAULT 120,
    consensus_percentage NUMERIC(5, 2) NOT NULL,
    leading_swarm VARCHAR(64),
    entry_price NUMERIC(15, 5),
    stop_loss NUMERIC(15, 5),
    take_profit NUMERIC(15, 5),
    swarm_summary JSONB DEFAULT '{}'::jsonb,
    swarm_details JSONB DEFAULT '{}'::jsonb,
    model_votes JSONB DEFAULT '{}'::jsonb,
    model_confidences JSONB DEFAULT '{}'::jsonb,
    is_executed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================================================================
-- TABLE 6: SYSTEM LOGS & REMOTE WEB-TO-MT5 COMMAND QUEUE
-- ====================================================================
CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    log_type VARCHAR(64) NOT NULL, -- 'REMOTE_COMMAND', 'BROADCAST_COMMAND', 'EA_HEARTBEAT', 'RISK_ALERT'
    severity VARCHAR(16) DEFAULT 'INFO', -- 'INFO', 'WARN', 'ERROR', 'CRITICAL'
    source VARCHAR(64) DEFAULT 'WEB_DASHBOARD',
    component VARCHAR(64) DEFAULT 'KESTREL_CORE',
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    payload JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================================================================
-- TABLE 7: PAYMENTS & CRYPTO CHECKOUT
-- ====================================================================
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    tier VARCHAR(32) NOT NULL, -- 'pro', 'enterprise', 'lifetime'
    amount_usd NUMERIC(10, 2) NOT NULL,
    crypto_currency VARCHAR(16) NOT NULL, -- 'USDT', 'BTC', 'ETH', 'SOL'
    deposit_address TEXT NOT NULL,
    tx_hash TEXT,
    status VARCHAR(32) DEFAULT 'PENDING', -- 'PENDING', 'CONFIRMED', 'EXPIRED'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================================================================
-- TABLE 8: CLIENT SUBSCRIPTIONS (PAMM COPY-TRADER RISK MATRIX)
-- ====================================================================
CREATE TABLE client_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_number VARCHAR(64) UNIQUE NOT NULL,
    client_name VARCHAR(128) NOT NULL,
    master_account_number VARCHAR(64) NOT NULL DEFAULT '41230754',
    risk_multiplier NUMERIC(4, 2) DEFAULT 1.00,
    is_copy_enabled BOOLEAN DEFAULT TRUE,
    max_drawdown_stop_pct NUMERIC(4, 2) DEFAULT 15.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================================================================
-- INDEXES FOR HIGH-SPEED QUERYING & LATENCY OPTIMIZATION
-- ====================================================================
CREATE INDEX IF NOT EXISTS idx_accounts_num ON accounts(account_number);
CREATE INDEX IF NOT EXISTS idx_accounts_license ON accounts(license_key);
CREATE INDEX IF NOT EXISTS idx_trades_account ON trades(account_number);
CREATE INDEX IF NOT EXISTS idx_trades_created ON trades(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_instrument ON signals(instrument);
CREATE INDEX IF NOT EXISTS idx_signals_created ON signals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_type ON system_logs(log_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ====================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES — OPEN READ/WRITE FOR CLOUD API & MT5
-- ====================================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE licenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_subscriptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read users" ON users FOR SELECT USING (true);
CREATE POLICY "Allow public insert users" ON users FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update users" ON users FOR UPDATE USING (true);

CREATE POLICY "Allow public read licenses" ON licenses FOR SELECT USING (true);
CREATE POLICY "Allow public insert licenses" ON licenses FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update licenses" ON licenses FOR UPDATE USING (true);

CREATE POLICY "Allow public read accounts" ON accounts FOR SELECT USING (true);
CREATE POLICY "Allow public insert accounts" ON accounts FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update accounts" ON accounts FOR UPDATE USING (true);

CREATE POLICY "Allow public read trades" ON trades FOR SELECT USING (true);
CREATE POLICY "Allow public insert trades" ON trades FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update trades" ON trades FOR UPDATE USING (true);

CREATE POLICY "Allow public read signals" ON signals FOR SELECT USING (true);
CREATE POLICY "Allow public insert signals" ON signals FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update signals" ON signals FOR UPDATE USING (true);

CREATE POLICY "Allow public read system_logs" ON system_logs FOR SELECT USING (true);
CREATE POLICY "Allow public insert system_logs" ON system_logs FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update system_logs" ON system_logs FOR UPDATE USING (true);

CREATE POLICY "Allow public read payments" ON payments FOR SELECT USING (true);
CREATE POLICY "Allow public insert payments" ON payments FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update payments" ON payments FOR UPDATE USING (true);

CREATE POLICY "Allow public read client_subscriptions" ON client_subscriptions FOR SELECT USING (true);
CREATE POLICY "Allow public insert client_subscriptions" ON client_subscriptions FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update client_subscriptions" ON client_subscriptions FOR UPDATE USING (true);

-- ====================================================================
-- SEED DATA: INITIAL MASTER & 5 REAL CLIENT ACCOUNTS
-- ====================================================================
INSERT INTO accounts (
    account_number, broker_name, server, license_key, license_tier, balance, equity, currency, total_profit, today_profit, recovery_multiplier, auto_trade_enabled, is_active
) VALUES 
('41230754', 'Deriv.com Limited (Master VIP)', 'Deriv-Demo', 'kestrel-enterprise-owner-vip', 'ENTERPRISE_MASTER', 10500.00, 10545.20, 'USD', 545.20, 45.20, 1.00, true, true),
('41890211', 'Deriv.com Limited (Alpha Prime Capital)', 'Deriv-Demo', 'user-alpha-prime', 'ENTERPRISE_CLIENT', 5250.00, 5272.50, 'USD', 272.50, 22.50, 1.00, true, true),
('41933842', 'Deriv.com Limited (Apex Wealth Management)', 'Deriv-Demo', 'user-apex-wealth', 'ENTERPRISE_CLIENT', 12800.00, 12860.00, 'USD', 680.00, 60.00, 1.20, true, true),
('41772109', 'Deriv.com Limited (Nexus Global Trader)', 'Deriv-Demo', 'user-nexus-global', 'ENTERPRISE_CLIENT', 3450.00, 3465.00, 'USD', 165.00, 15.00, 0.80, true, true),
('41655430', 'Deriv.com Limited (Titanium Index Fund)', 'Deriv-Demo', 'user-titanium-fund', 'ENTERPRISE_CLIENT', 25000.00, 25120.00, 'USD', 1420.00, 120.00, 1.50, true, true),
('41509823', 'Deriv.com Limited (Zenith Syndicate)', 'Deriv-Demo', 'user-zenith-syndicate', 'ENTERPRISE_CLIENT', 8750.00, 8785.00, 'USD', 435.00, 35.00, 1.00, true, true)
ON CONFLICT (account_number) DO UPDATE SET 
    balance = EXCLUDED.balance,
    equity = EXCLUDED.equity,
    updated_at = NOW();

-- SEED CLIENT SUBSCRIPTION RISK MATRIX
INSERT INTO client_subscriptions (client_account_number, client_name, master_account_number, risk_multiplier, is_copy_enabled, max_drawdown_stop_pct)
VALUES
('41890211', 'Alpha Prime Capital', '41230754', 1.00, true, 15.00),
('41933842', 'Apex Wealth Management', '41230754', 1.20, true, 12.00),
('41772109', 'Nexus Global Trader', '41230754', 0.80, true, 10.00),
('41655430', 'Titanium Index Fund', '41230754', 1.50, true, 20.00),
('41509823', 'Zenith Syndicate', '41230754', 1.00, true, 15.00)
ON CONFLICT (client_account_number) DO UPDATE SET 
    risk_multiplier = EXCLUDED.risk_multiplier,
    updated_at = NOW();
