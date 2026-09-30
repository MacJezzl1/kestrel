-- ====================================================================
-- MIGRATION 005: NOTIFICATION WEBHOOKS & MULTI-BROKER COPIER HUB
-- ====================================================================
-- Description:
-- 1. notification_configs: Stores Telegram bot token, chat ID, and Discord webhook URLs per user/tenant.
-- 2. copier_accounts: Configures multi-broker receiver routing, risk multipliers (0.1x - 5.0x), and limits.
-- 3. Enables Row-Level Security (RLS) with tenant isolation policies.
-- ====================================================================

-- +goose Up
-- +migrate Up
-- ────────────────────────────────────────────────────────────────────
-- 1. NOTIFICATION CONFIGS TABLE
-- ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notification_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000001'::uuid,
    user_id VARCHAR(64) NOT NULL,
    telegram_enabled BOOLEAN DEFAULT FALSE,
    telegram_bot_token VARCHAR(255),
    telegram_chat_id VARCHAR(128),
    discord_enabled BOOLEAN DEFAULT FALSE,
    discord_webhook_url TEXT,
    alert_trade_signals BOOLEAN DEFAULT TRUE,
    alert_prop_firm_risk BOOLEAN DEFAULT TRUE,
    alert_circuit_breaker BOOLEAN DEFAULT TRUE,
    alert_high_impact_news BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_notif_tenant_user UNIQUE (tenant_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_notif_tenant ON notification_configs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_notif_user ON notification_configs(user_id);

-- ────────────────────────────────────────────────────────────────────
-- 2. COPIER ACCOUNTS TABLE (MULTI-BROKER HUB)
-- ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS copier_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000001'::uuid,
    account_login VARCHAR(64) NOT NULL,
    account_name VARCHAR(128) NOT NULL,
    broker_profile VARCHAR(64) NOT NULL,
    role VARCHAR(20) DEFAULT 'RECEIVER',
    risk_multiplier NUMERIC(4, 2) DEFAULT 1.00,
    max_lot_cap NUMERIC(10, 2) DEFAULT 5.00,
    max_slippage_pips NUMERIC(6, 2) DEFAULT 3.00,
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_copier_tenant_login UNIQUE (tenant_id, account_login)
);

CREATE INDEX IF NOT EXISTS idx_copier_tenant ON copier_accounts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_copier_role ON copier_accounts(role);
CREATE INDEX IF NOT EXISTS idx_copier_broker ON copier_accounts(broker_profile);

-- ────────────────────────────────────────────────────────────────────
-- 3. ENABLE ROW-LEVEL SECURITY & APPLY TENANT POLICIES
-- ────────────────────────────────────────────────────────────────────
ALTER TABLE notification_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE copier_accounts ENABLE ROW LEVEL SECURITY;

DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN SELECT unnest(ARRAY['notification_configs', 'copier_accounts'])
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
    FOR tbl IN SELECT unnest(ARRAY['notification_configs', 'copier_accounts'])
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
DROP TABLE IF EXISTS copier_accounts CASCADE;
DROP TABLE IF EXISTS notification_configs CASCADE;
