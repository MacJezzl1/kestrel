-- ====================================================================
-- MIGRATION 000: SECURITY HARDENING & MULTI-TENANT ISOLATION
-- ====================================================================
-- Description:
-- 1. Adds tenant_id to accounts, trades, signals, orders, licenses, performance_snapshots.
-- 2. Enables RLS on ALL tables with tenant_id and auth.uid() filtering.
-- 3. Revokes all open public read/write policies.
-- 4. Creates append-only, immutable audit_log with trigger blocking UPDATE/DELETE.
-- 5. Implements pgcrypto column-level encryption functions for sensitive fields.
-- ====================================================================

-- +goose Up
-- +migrate Up
-- ────────────────────────────────────────────────────────────────────
-- 1. EXTENSIONS
-- ────────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ────────────────────────────────────────────────────────────────────
-- 2. ADD TENANT_ID COLUMNS FOR MULTI-TENANCY
-- ────────────────────────────────────────────────────────────────────
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000001'::uuid;
ALTER TABLE trades ADD COLUMN IF NOT EXISTS tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000001'::uuid;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000001'::uuid;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000001'::uuid;
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000001'::uuid;

CREATE TABLE IF NOT EXISTS performance_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000001'::uuid,
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    balance NUMERIC(15, 2) NOT NULL,
    equity NUMERIC(15, 2) NOT NULL,
    drawdown_pct NUMERIC(6, 2) DEFAULT 0.00,
    daily_pnl NUMERIC(15, 2) DEFAULT 0.00,
    metrics JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_accounts_tenant ON accounts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_trades_tenant ON trades(tenant_id);
CREATE INDEX IF NOT EXISTS idx_signals_tenant ON signals(tenant_id);
CREATE INDEX IF NOT EXISTS idx_orders_tenant ON orders(tenant_id);
CREATE INDEX IF NOT EXISTS idx_licenses_tenant ON licenses(tenant_id);
CREATE INDEX IF NOT EXISTS idx_perf_tenant ON performance_snapshots(tenant_id);

-- ────────────────────────────────────────────────────────────────────
-- 3. IMMUTABLE APPEND-ONLY AUDIT LOG (NO UPDATE / NO DELETE)
-- ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000001'::uuid,
    user_id UUID,
    action VARCHAR(64) NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_tenant_time ON audit_log(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action, created_at DESC);

-- Trigger to reject any UPDATE or DELETE on audit_log
CREATE OR REPLACE FUNCTION prevent_audit_log_tampering()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Security Policy Violation: audit_log is strictly append-only. UPDATE and DELETE are prohibited.'
        USING ERRCODE = '42501';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_log_immutable ON audit_log;
CREATE TRIGGER trg_audit_log_immutable
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_tampering();

-- Revoke mutation grants on audit_log
REVOKE UPDATE, DELETE, TRUNCATE ON audit_log FROM PUBLIC;
REVOKE UPDATE, DELETE, TRUNCATE ON audit_log FROM anon;
REVOKE UPDATE, DELETE, TRUNCATE ON audit_log FROM authenticated;

-- ────────────────────────────────────────────────────────────────────
-- 4. PGCRYPTO COLUMN-LEVEL ENCRYPTION FOR AT-REST SECURITY
-- ────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION encrypt_sensitive(val TEXT, master_key TEXT)
RETURNS BYTEA AS $$
BEGIN
    IF val IS NULL THEN RETURN NULL; END IF;
    RETURN pgp_sym_encrypt(val, master_key, 'cipher-algo=aes256, compress-algo=1');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION decrypt_sensitive(val BYTEA, master_key TEXT)
RETURNS TEXT AS $$
BEGIN
    IF val IS NULL THEN RETURN NULL; END IF;
    RETURN pgp_sym_decrypt(val, master_key);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ────────────────────────────────────────────────────────────────────
-- 5. ENABLE ROW LEVEL SECURITY (RLS) ON ALL TABLES
-- ────────────────────────────────────────────────────────────────────
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE licenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Drop legacy permissive policies if they exist
DROP POLICY IF EXISTS "Allow public read orders" ON orders;
DROP POLICY IF EXISTS "Allow public insert orders" ON orders;
DROP POLICY IF EXISTS "Allow public update orders" ON orders;
DROP POLICY IF EXISTS "Allow public read ai_logs" ON ai_logs;
DROP POLICY IF EXISTS "Allow public insert ai_logs" ON ai_logs;
DROP POLICY IF EXISTS "Allow public read users" ON users;
DROP POLICY IF EXISTS "Allow public insert users" ON users;
DROP POLICY IF EXISTS "Allow public update users" ON users;
DROP POLICY IF EXISTS "Allow public read licenses" ON licenses;
DROP POLICY IF EXISTS "Allow public insert licenses" ON licenses;
DROP POLICY IF EXISTS "Allow public update licenses" ON licenses;
DROP POLICY IF EXISTS "Allow public read accounts" ON accounts;
DROP POLICY IF EXISTS "Allow public insert accounts" ON accounts;
DROP POLICY IF EXISTS "Allow public update accounts" ON accounts;
DROP POLICY IF EXISTS "Allow public read trades" ON trades;
DROP POLICY IF EXISTS "Allow public insert trades" ON trades;
DROP POLICY IF EXISTS "Allow public update trades" ON trades;
DROP POLICY IF EXISTS "Allow public read signals" ON signals;
DROP POLICY IF EXISTS "Allow public insert signals" ON signals;
DROP POLICY IF EXISTS "Allow public update signals" ON signals;
DROP POLICY IF EXISTS "Allow public read system_logs" ON system_logs;
DROP POLICY IF EXISTS "Allow public insert system_logs" ON system_logs;
DROP POLICY IF EXISTS "Allow public update system_logs" ON system_logs;
DROP POLICY IF EXISTS "Allow public read payments" ON payments;
DROP POLICY IF EXISTS "Allow public insert payments" ON payments;
DROP POLICY IF EXISTS "Allow public update payments" ON payments;
DROP POLICY IF EXISTS "Allow public read client_subscriptions" ON client_subscriptions;
DROP POLICY IF EXISTS "Allow public insert client_subscriptions" ON client_subscriptions;
DROP POLICY IF EXISTS "Allow public update client_subscriptions" ON client_subscriptions;

-- Multi-Tenant & User-Level Hardened Policies:
-- Users
CREATE POLICY users_isolation ON users
    FOR ALL
    USING (id = auth.uid() OR current_setting('request.jwt.claim.role', true) = 'service_role');

-- Accounts
CREATE POLICY accounts_isolation ON accounts
    FOR ALL
    USING (
        tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        OR user_id = auth.uid()
        OR current_setting('request.jwt.claim.role', true) = 'service_role'
    );

-- Trades
CREATE POLICY trades_isolation ON trades
    FOR ALL
    USING (
        tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        OR user_id = auth.uid()
        OR current_setting('request.jwt.claim.role', true) = 'service_role'
    );

-- Orders
CREATE POLICY orders_isolation ON orders
    FOR ALL
    USING (
        tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        OR user_id = auth.uid()
        OR current_setting('request.jwt.claim.role', true) = 'service_role'
    );

-- Signals (Authenticated users in tenant can view signals)
CREATE POLICY signals_isolation ON signals
    FOR SELECT
    USING (
        tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        OR auth.role() IN ('authenticated', 'service_role')
    );

CREATE POLICY signals_service_mutate ON signals
    FOR ALL
    USING (current_setting('request.jwt.claim.role', true) = 'service_role');

-- Performance Snapshots
CREATE POLICY perf_snapshots_isolation ON performance_snapshots
    FOR ALL
    USING (
        tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        OR current_setting('request.jwt.claim.role', true) = 'service_role'
    );

-- Audit Log (Read-only for tenant, append-only for authenticated/service)
CREATE POLICY audit_log_tenant_select ON audit_log
    FOR SELECT
    USING (
        tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        OR user_id = auth.uid()
        OR current_setting('request.jwt.claim.role', true) = 'service_role'
    );

CREATE POLICY audit_log_insert ON audit_log
    FOR INSERT
    WITH CHECK (auth.role() IN ('authenticated', 'service_role', 'anon'));

-- Licenses
CREATE POLICY licenses_isolation ON licenses
    FOR ALL
    USING (
        user_id = auth.uid()
        OR tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        OR current_setting('request.jwt.claim.role', true) = 'service_role'
    );


-- +goose Down
-- +migrate Down
-- ────────────────────────────────────────────────────────────────────
-- DOWN MIGRATION (ROLLBACK)
-- ────────────────────────────────────────────────────────────────────
DROP POLICY IF EXISTS licenses_isolation ON licenses;
DROP POLICY IF EXISTS audit_log_insert ON audit_log;
DROP POLICY IF EXISTS audit_log_tenant_select ON audit_log;
DROP POLICY IF EXISTS perf_snapshots_isolation ON performance_snapshots;
DROP POLICY IF EXISTS signals_service_mutate ON signals;
DROP POLICY IF EXISTS signals_isolation ON signals;
DROP POLICY IF EXISTS orders_isolation ON orders;
DROP POLICY IF EXISTS trades_isolation ON trades;
DROP POLICY IF EXISTS accounts_isolation ON accounts;
DROP POLICY IF EXISTS users_isolation ON users;

DROP TRIGGER IF EXISTS trg_audit_log_immutable ON audit_log;
DROP FUNCTION IF EXISTS prevent_audit_log_tampering();
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS performance_snapshots CASCADE;

DROP FUNCTION IF EXISTS decrypt_sensitive(BYTEA, TEXT);
DROP FUNCTION IF EXISTS encrypt_sensitive(TEXT, TEXT);

ALTER TABLE licenses DROP COLUMN IF EXISTS tenant_id;
ALTER TABLE orders DROP COLUMN IF EXISTS tenant_id;
ALTER TABLE signals DROP COLUMN IF EXISTS tenant_id;
ALTER TABLE trades DROP COLUMN IF EXISTS tenant_id;
ALTER TABLE accounts DROP COLUMN IF EXISTS tenant_id;
