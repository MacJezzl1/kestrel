-- ====================================================================
-- MIGRATION 003: ADD ECONOMIC EVENTS CALENDAR TABLE
-- ====================================================================
-- Description:
-- Creates economic_events table for high-impact news filtering and volatility guard.
-- Provides automated indexing on event_time_utc and impact level.
-- ====================================================================

-- +goose Up
-- +migrate Up
CREATE TABLE IF NOT EXISTS economic_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID DEFAULT '00000000-0000-0000-0000-000000000001'::uuid,
    event_time_utc TIMESTAMPTZ NOT NULL,
    country VARCHAR(16) NOT NULL DEFAULT 'USD',
    currency VARCHAR(8) NOT NULL DEFAULT 'USD',
    impact VARCHAR(16) NOT NULL DEFAULT 'HIGH', -- 'HIGH', 'MEDIUM', 'LOW', 'NONE'
    title VARCHAR(255) NOT NULL,
    forecast VARCHAR(64),
    previous VARCHAR(64),
    actual VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_economic_events_time ON economic_events(event_time_utc);
CREATE INDEX IF NOT EXISTS idx_economic_events_impact_time ON economic_events(impact, event_time_utc);

-- Enable RLS
ALTER TABLE economic_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY economic_events_read ON economic_events FOR SELECT USING (true);
CREATE POLICY economic_events_service ON economic_events FOR ALL USING (current_setting('request.jwt.claim.role', true) = 'service_role');

-- +goose Down
-- +migrate Down
DROP POLICY IF EXISTS economic_events_service ON economic_events;
DROP POLICY IF EXISTS economic_events_read ON economic_events;
DROP TABLE IF EXISTS economic_events CASCADE;
