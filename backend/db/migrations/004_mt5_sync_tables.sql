-- ====================================================================
-- MIGRATION 004: MT5 SYNC, LIVE POSITIONS, RISK METRICS & REMOTE COMMANDS
-- ====================================================================
-- Description:
-- 1. mt5_terminals: Hardware-bound MT5 client terminals, account details & heartbeat telemetry.
-- 2. live_positions: Real-time open position tracking with floating PnL and ticket confluences.
-- 3. risk_metrics: Account-level risk limits, daily loss % & prop-firm circuit breakers.
-- 4. remote_commands: Command queue for Web->MT5 remote orders (BUY/SELL/CLOSE/CLOSE_ALL).
-- 5. copy_trades: Multi-client PAMM broadcast log tracking receiver execution, latency, and slippage.
-- 6. Enables Row-Level Security (RLS) on all tables with tenant isolation.
-- ====================================================================

-- +goose Up
-- +migrate Up
-- ────────────────────────────────────────────────────────────────────
-- 1. MT5 TERMINALS TABLE
-- ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mt5_terminals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000001'::uuid,
    user_id UUID,
    account_login VARCHAR(64) NOT NULL,
    terminal_hash VARCHAR(128) NOT NULL,
    broker VARCHAR(128),
    server VARCHAR(128),
    currency VARCHAR(16) DEFAULT 'USD',
    leverage INT DEFAULT 100,
    balance NUMERIC(15, 2) DEFAULT 0.00,
    equity NUMERIC(15, 2) DEFAULT 0.00,
    margin NUMERIC(15, 2) DEFAULT 0.00,
    free_margin NUMERIC(15, 2) DEFAULT 0.00,
    margin_level NUMERIC(8, 2) DEFAULT 0.00,
    ping_latency_ms INT DEFAULT 0,
    regime VARCHAR(64) DEFAULT 'REGIME_HYBRID',
    ea_version VARCHAR(32) DEFAULT '4.00',
    is_active BOOLEAN DEFAULT TRUE,
    last_heartbeat TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_terminal_account UNIQUE (tenant_id, account_login)
);

CREATE INDEX IF NOT EXISTS idx_mt5_terminals_tenant ON mt5_terminals(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mt5_terminals_login ON mt5_terminals(account_login);
CREATE INDEX IF NOT EXISTS idx_mt5_terminals_hash ON mt5_terminals(terminal_hash);
CREATE INDEX IF NOT EXISTS idx_mt5_terminals_heartbeat ON mt5_terminals(last_heartbeat DESC);

-- ────────────────────────────────────────────────────────────────────
-- 2. LIVE POSITIONS TABLE
-- ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS live_positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000001'::uuid,
    terminal_id UUID REFERENCES mt5_terminals(id) ON DELETE CASCADE,
    account_login VARCHAR(64) NOT NULL,
    ticket BIGINT NOT NULL,
    magic_number BIGINT DEFAULT 773571,
    symbol VARCHAR(32) NOT NULL,
    direction VARCHAR(16) NOT NULL,
    lots NUMERIC(10, 2) NOT NULL,
    open_price NUMERIC(15, 5) NOT NULL,
    current_price NUMERIC(15, 5) NOT NULL,
    stop_loss NUMERIC(15, 5),
    take_profit NUMERIC(15, 5),
    floating_pnl NUMERIC(15, 2) DEFAULT 0.00,
    pnl_pips NUMERIC(10, 2) DEFAULT 0.00,
    swap NUMERIC(15, 2) DEFAULT 0.00,
    commission NUMERIC(15, 2) DEFAULT 0.00,
    comment VARCHAR(255),
    open_time TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_pos_terminal_ticket UNIQUE (terminal_id, ticket)
);

CREATE INDEX IF NOT EXISTS idx_live_pos_tenant ON live_positions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_live_pos_terminal ON live_positions(terminal_id);
CREATE INDEX IF NOT EXISTS idx_live_pos_ticket ON live_positions(ticket);
CREATE INDEX IF NOT EXISTS idx_live_pos_symbol ON live_positions(symbol);

-- ────────────────────────────────────────────────────────────────────
-- 3. RISK METRICS TABLE
-- ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS risk_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000001'::uuid,
    terminal_id UUID REFERENCES mt5_terminals(id) ON DELETE CASCADE,
    account_login VARCHAR(64) NOT NULL,
    starting_equity_day NUMERIC(15, 2) NOT NULL,
    peak_equity NUMERIC(15, 2) NOT NULL,
    current_equity NUMERIC(15, 2) NOT NULL,
    current_balance NUMERIC(15, 2) NOT NULL,
    daily_loss_pct NUMERIC(6, 2) DEFAULT 0.00,
    max_drawdown_pct NUMERIC(6, 2) DEFAULT 0.00,
    consecutive_losses INT DEFAULT 0,
    circuit_breaker_tripped BOOLEAN DEFAULT FALSE,
    prop_rule_breach BOOLEAN DEFAULT FALSE,
    prop_firm_profile VARCHAR(32) DEFAULT 'PROP_NONE',
    reset_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_risk_metrics_terminal UNIQUE (terminal_id)
);

CREATE INDEX IF NOT EXISTS idx_risk_metrics_tenant ON risk_metrics(tenant_id);
CREATE INDEX IF NOT EXISTS idx_risk_metrics_login ON risk_metrics(account_login);

-- ────────────────────────────────────────────────────────────────────
-- 4. REMOTE COMMANDS TABLE (WEB -> MT5 QUEUE)
-- ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS remote_commands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000001'::uuid,
    terminal_id UUID REFERENCES mt5_terminals(id) ON DELETE CASCADE,
    account_login VARCHAR(64) NOT NULL,
    command_type VARCHAR(32) NOT NULL,
    symbol VARCHAR(32),
    ticket BIGINT,
    lots NUMERIC(10, 2),
    price NUMERIC(15, 5),
    stop_loss NUMERIC(15, 5),
    take_profit NUMERIC(15, 5),
    status VARCHAR(20) DEFAULT 'PENDING',
    result JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    executed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_remote_cmd_tenant ON remote_commands(tenant_id);
CREATE INDEX IF NOT EXISTS idx_remote_cmd_terminal_status ON remote_commands(terminal_id, status);
CREATE INDEX IF NOT EXISTS idx_remote_cmd_created ON remote_commands(created_at DESC);

-- ────────────────────────────────────────────────────────────────────
-- 5. COPY TRADES TABLE (PAMM MASTER-RECEIVER LOG)
-- ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS copy_trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000001'::uuid,
    master_ticket BIGINT NOT NULL,
    master_symbol VARCHAR(32) NOT NULL,
    master_direction VARCHAR(16) NOT NULL,
    master_lots NUMERIC(10, 2) NOT NULL,
    receiver_terminal_id UUID REFERENCES mt5_terminals(id) ON DELETE CASCADE,
    receiver_account VARCHAR(64) NOT NULL,
    receiver_ticket BIGINT,
    risk_multiplier NUMERIC(4, 2) DEFAULT 1.00,
    executed_lots NUMERIC(10, 2),
    execution_price NUMERIC(15, 5),
    slippage_pips NUMERIC(6, 2) DEFAULT 0.00,
    latency_ms INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'PENDING',
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    executed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_copy_trades_tenant ON copy_trades(tenant_id);
CREATE INDEX IF NOT EXISTS idx_copy_trades_master ON copy_trades(master_ticket);
CREATE INDEX IF NOT EXISTS idx_copy_trades_receiver ON copy_trades(receiver_terminal_id, status);

-- ────────────────────────────────────────────────────────────────────
-- 6. ENABLE ROW-LEVEL SECURITY & APPLY TENANT POLICIES
-- ────────────────────────────────────────────────────────────────────
ALTER TABLE mt5_terminals ENABLE ROW LEVEL SECURITY;
ALTER TABLE live_positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE remote_commands ENABLE ROW LEVEL SECURITY;
ALTER TABLE copy_trades ENABLE ROW LEVEL SECURITY;

-- Tenant Isolation Policies
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN SELECT unnest(ARRAY['mt5_terminals', 'live_positions', 'risk_metrics', 'remote_commands', 'copy_trades'])
    LOOP
        EXECUTE format('
            DROP POLICY IF EXISTS %I_tenant_isolation ON %I;
            CREATE POLICY %I_tenant_isolation ON %I
                FOR ALL
                USING (
                    tenant_id = NULLIF(current_setting(''app.current_tenant_id'', true), '''')::uuid
                    OR current_setting(''role'', true) IN (''service_role'', ''postgres'')
                    OR auth.role() = ''service_role''
                )
                WITH CHECK (
                    tenant_id = NULLIF(current_setting(''app.current_tenant_id'', true), '''')::uuid
                    OR current_setting(''role'', true) IN (''service_role'', ''postgres'')
                    OR auth.role() = ''service_role''
                );
        ', tbl, tbl, tbl, tbl);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Service role bypass
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN SELECT unnest(ARRAY['mt5_terminals', 'live_positions', 'risk_metrics', 'remote_commands', 'copy_trades'])
    LOOP
        EXECUTE format('
            DROP POLICY IF EXISTS %I_service_role ON %I;
            CREATE POLICY %I_service_role ON %I
                FOR ALL
                TO service_role
                USING (true)
                WITH CHECK (true);
        ', tbl, tbl, tbl, tbl);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- +goose Down
-- +migrate Down
DROP TABLE IF EXISTS copy_trades CASCADE;
DROP TABLE IF EXISTS remote_commands CASCADE;
DROP TABLE IF EXISTS risk_metrics CASCADE;
DROP TABLE IF EXISTS live_positions CASCADE;
DROP TABLE IF EXISTS mt5_terminals CASCADE;
