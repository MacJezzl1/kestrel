-- ====================================================================
-- Kestrel AI Trading Intelligence System — Supabase PostgreSQL Schema
-- Organization: CapeChain Labs
-- Project: https://supabase.com/dashboard/org/qbdmnpjvkllktwkoqeow
-- ====================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. ACCOUNTS & LICENSES TABLE
CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_number VARCHAR(64) UNIQUE NOT NULL,
    broker_name VARCHAR(128) DEFAULT 'MetaTrader 5',
    license_key VARCHAR(128) NOT NULL,
    license_tier VARCHAR(32) DEFAULT 'PRO_ENTERPRISE', -- BASIC, PRO, ENTERPRISE
    balance NUMERIC(15, 2) DEFAULT 0.00,
    equity NUMERIC(15, 2) DEFAULT 0.00,
    currency VARCHAR(8) DEFAULT 'USD',
    initial_balance NUMERIC(15, 2) DEFAULT 0.00,
    total_profit NUMERIC(15, 2) DEFAULT 0.00,
    today_profit NUMERIC(15, 2) DEFAULT 0.00,
    max_drawdown_pct NUMERIC(6, 2) DEFAULT 0.00,
    current_drawdown_pct NUMERIC(6, 2) DEFAULT 0.00,
    recovery_level VARCHAR(32) DEFAULT 'OPTIMAL', -- OPTIMAL, CAUTION, RECOVERY_SHIELD, AGGRESSIVE_RECOVERY
    recovery_multiplier NUMERIC(4, 2) DEFAULT 1.00,
    auto_trade_enabled BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. TRADES & EXECUTION LOGS TABLE
CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
    mt5_ticket BIGINT,
    instrument VARCHAR(32) NOT NULL, -- e.g. USDJPY, EURUSD, XAUUSD
    timeframe VARCHAR(16) DEFAULT 'H1',
    direction VARCHAR(8) NOT NULL, -- BUY, SELL
    lot_size NUMERIC(8, 2) NOT NULL DEFAULT 0.01,
    entry_price NUMERIC(15, 5) NOT NULL,
    exit_price NUMERIC(15, 5),
    stop_loss NUMERIC(15, 5),
    take_profit NUMERIC(15, 5),
    profit_amount NUMERIC(15, 2) DEFAULT 0.00,
    profit_pips NUMERIC(10, 2) DEFAULT 0.00,
    confidence_at_entry NUMERIC(5, 4),
    swarm_consensus_pct NUMERIC(5, 2),
    market_regime VARCHAR(32),
    recovery_tag VARCHAR(64) DEFAULT 'STANDARD_ENTRY',
    execution_status VARCHAR(32) DEFAULT 'OPEN', -- OPEN, CLOSED, CANCELLED, REJECTED
    closed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 3. AI 100-MODEL REGISTRY TABLE
CREATE TABLE IF NOT EXISTS ai_models (
    id VARCHAR(64) PRIMARY KEY, -- e.g. macro_dxy_flow_01, quant_kalman_05
    swarm_category VARCHAR(64) NOT NULL, -- MACRO_GEOPOLITICAL, PRICE_ACTION_MICRO, STAT_ARB_QUANT, MOMENTUM_FLOW, SENTIMENT_REASONING
    model_name VARCHAR(128) NOT NULL,
    description TEXT,
    accuracy_score NUMERIC(5, 2) DEFAULT 75.00,
    weight NUMERIC(5, 4) DEFAULT 1.0000,
    is_active BOOLEAN DEFAULT TRUE,
    total_votes_cast BIGINT DEFAULT 0,
    successful_predictions BIGINT DEFAULT 0,
    latency_ms INT DEFAULT 12,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 100-AI SWARM CONSENSUS & SIGNALS TABLE
CREATE TABLE IF NOT EXISTS signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instrument VARCHAR(32) NOT NULL,
    timeframe VARCHAR(16) NOT NULL,
    direction VARCHAR(8) NOT NULL, -- BUY, SELL, HOLD
    confidence NUMERIC(5, 4) NOT NULL, -- e.g. 0.875
    regime VARCHAR(32) NOT NULL, -- TRENDING_BULL, TRENDING_BEAR, RANGING, VOLATILE_BREAKOUT
    buy_votes INT DEFAULT 0,
    sell_votes INT DEFAULT 0,
    hold_votes INT DEFAULT 0,
    total_models INT DEFAULT 100,
    consensus_percentage NUMERIC(5, 2) NOT NULL,
    leading_swarm VARCHAR(64),
    entry_price NUMERIC(15, 5),
    stop_loss NUMERIC(15, 5),
    take_profit NUMERIC(15, 5),
    swarm_details JSONB DEFAULT '{}'::jsonb, -- Breakdown of votes across all 5 swarms (20 models each)
    is_executed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. RECOVERY METRICS & PERFORMANCE SNAPSHOTS TABLE
CREATE TABLE IF NOT EXISTS performance_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    balance NUMERIC(15, 2) NOT NULL,
    equity NUMERIC(15, 2) NOT NULL,
    daily_pnl NUMERIC(15, 2) NOT NULL,
    total_pnl NUMERIC(15, 2) NOT NULL,
    win_rate_pct NUMERIC(5, 2) DEFAULT 0.00,
    profit_factor NUMERIC(6, 2) DEFAULT 1.00,
    recovery_level VARCHAR(32) DEFAULT 'OPTIMAL',
    current_drawdown_pct NUMERIC(6, 2) DEFAULT 0.00
);

-- 6. SYSTEM AUDIT & ADAPTER LOGS TABLE
CREATE TABLE IF NOT EXISTS system_logs (
    id BIGSERIAL PRIMARY KEY,
    component VARCHAR(64) NOT NULL, -- MT5_ADAPTER, BACKEND_CORE, SWARM_100, SUPABASE_SYNC
    level VARCHAR(16) DEFAULT 'INFO', -- INFO, WARN, ERROR, SUCCESS
    message TEXT NOT NULL,
    payload JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ====================================================================
-- INDEXES FOR FAST QUERYING
-- ====================================================================
CREATE INDEX IF NOT EXISTS idx_trades_account_id ON trades(account_id);
CREATE INDEX IF NOT EXISTS idx_trades_instrument ON trades(instrument);
CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_instrument_tf ON signals(instrument, timeframe, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_models_category ON ai_models(swarm_category);
CREATE INDEX IF NOT EXISTS idx_performance_snapshots_account ON performance_snapshots(account_id, timestamp DESC);

-- ====================================================================
-- REALTIME REPLICATION (Supabase Realtime)
-- ====================================================================
-- Enable realtime for key streaming tables
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'supabase_realtime') THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE accounts;
        ALTER PUBLICATION supabase_realtime ADD TABLE trades;
        ALTER PUBLICATION supabase_realtime ADD TABLE signals;
        ALTER PUBLICATION supabase_realtime ADD TABLE performance_snapshots;
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        NULL;
END $$;

-- ====================================================================
-- ROW LEVEL SECURITY (RLS)
-- ====================================================================
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_logs ENABLE ROW LEVEL SECURITY;

-- Allow read/write access via API keys
CREATE POLICY "Allow public read access to active models" ON ai_models
    FOR SELECT USING (is_active = true);

CREATE POLICY "Allow service role full access to accounts" ON accounts
    FOR ALL USING (true);

CREATE POLICY "Allow service role full access to trades" ON trades
    FOR ALL USING (true);

CREATE POLICY "Allow service role full access to signals" ON signals
    FOR ALL USING (true);

CREATE POLICY "Allow service role full access to snapshots" ON performance_snapshots
    FOR ALL USING (true);

CREATE POLICY "Allow service role full access to logs" ON system_logs
    FOR ALL USING (true);
