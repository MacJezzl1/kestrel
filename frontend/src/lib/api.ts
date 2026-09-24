/**
 * Kestrel API Client
 * Centralized HTTP client for all backend API calls.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  isFormData?: boolean;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('kestrel_token');
  }

  async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body, headers = {}, isFormData = false } = options;
    
    const token = this.getToken();
    const reqHeaders: Record<string, string> = {
      ...headers,
    };

    if (token) {
      reqHeaders['Authorization'] = `Bearer ${token}`;
    }

    if (!isFormData) {
      reqHeaders['Content-Type'] = 'application/json';
    }

    const config: RequestInit = {
      method,
      headers: reqHeaders,
    };

    if (body) {
      config.body = isFormData ? (body as FormData) : JSON.stringify(body);
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, config);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new ApiError(response.status, error.detail || 'Unknown error');
    }

    return response.json();
  }

  // Auth
  async register(email: string, password: string, fullName?: string) {
    return this.request<AuthResponse>('/api/auth/register', {
      method: 'POST',
      body: { email, password, full_name: fullName },
    });
  }

  async login(email: string, password: string) {
    return this.request<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: { email, password },
    });
  }

  async getProfile() {
    return this.request<UserProfile>('/api/auth/me');
  }

  async getLicense() {
    return this.request<LicenseInfo>('/api/auth/license');
  }

  // Security
  async getSessions() {
    return this.request<SessionInfo[]>('/api/security/sessions');
  }

  async revokeAllSessions() {
    return this.request<{ message: string; access_token: string }>('/api/security/sessions/revoke-all', {
      method: 'POST',
    });
  }

  async changePassword(currentPassword: string, newPassword: string) {
    return this.request<{ message: string; access_token: string }>('/api/security/change-password', {
      method: 'POST',
      body: { current_password: currentPassword, new_password: newPassword },
    });
  }

  async createApiKey(name: string, permissions: string[] = ['signals', 'trades']) {
    return this.request<ApiKeyCreated>('/api/security/api-keys', {
      method: 'POST',
      body: { name, permissions },
    });
  }

  async listApiKeys() {
    return this.request<ApiKeyInfo[]>('/api/security/api-keys');
  }

  async revokeApiKey(keyId: string) {
    return this.request<{ message: string }>(`/api/security/api-keys/${keyId}`, {
      method: 'DELETE',
    });
  }

  async getAuditLog(limit: number = 50, offset: number = 0) {
    return this.request<AuditLogEntry[]>(`/api/security/audit-log?limit=${limit}&offset=${offset}`);
  }

  // Broker Account Linker
  async linkBrokerAccount(data: { account_number: string; broker_name: string; server: string; balance?: number; currency?: string }) {
    return this.request<{ status: string; message: string; account: any }>('/api/auth/link-broker', {
      method: 'POST',
      body: data,
    });
  }

  async getBrokerInfo() {
    return this.request<{ account_number: string; broker_name: string; server: string; balance: number; equity: number; currency: string }>('/api/auth/broker-info');
  }

  // Dashboard
  async getDashboardSummary() {
    return this.request<DashboardSummary>('/api/dashboard/summary');
  }

  async getDrawdown() {
    return this.request<DrawdownInfo>('/api/dashboard/drawdown');
  }

  async getPLBreakdown() {
    return this.request<PLBreakdown>('/api/dashboard/pnl-breakdown');
  }

  // Signals
  async generateSignal(instrument: string, timeframe: string = 'H1') {
    return this.request<Signal>('/api/signals/generate', {
      method: 'POST',
      body: { instrument, timeframe },
    });
  }

  async getLatestSignals(limit: number = 20, instrument?: string) {
    const params = new URLSearchParams({ limit: String(limit) });
    if (instrument) params.set('instrument', instrument);
    return this.request<SignalList>(`/api/signals/latest?${params}`);
  }

  async getSignal(id: string) {
    return this.request<Signal>(`/api/signals/${id}`);
  }

  // Trades
  async getTrades(limit = 50, offset = 0, status?: string, instrument?: string) {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (status) params.set('status', status);
    if (instrument) params.set('instrument', instrument);
    return this.request<TradeList>(`/api/trades?${params}`);
  }

  async createTrade(data: TradeCreate) {
    return this.request<Trade>('/api/trades', { method: 'POST', body: data });
  }

  async getTradeStats() {
    return this.request<TradeStats>('/api/trades/stats');
  }

  async pushWebTrade(data: { action: string; instrument: string; lot_size: number; sl?: number; tp?: number }) {
    return this.request<{ status: string; message: string }>('/api/trades/web-push', {
      method: 'POST',
      body: data,
    });
  }

  // Multi-Client Copy-Trader Hub
  async getClients() {
    return this.request<{
      summary: {
        total_clients: number;
        active_clients: number;
        total_aum_usd: number;
        total_equity_usd: number;
        floating_profit_usd: number;
        total_realized_profit: number;
        today_profit: number;
        swarm_status: string;
        sync_latency_ms: number;
      };
      clients: Array<{
        id: string;
        account_number: string;
        broker_name: string;
        license_tier: string;
        balance: number;
        equity: number;
        currency: string;
        total_profit: number;
        today_profit: number;
        recovery_multiplier: number;
        auto_trade_enabled: boolean;
        is_active: boolean;
      }>;
    }>('/api/clients');
  }

  async broadcastTrade(data: { action: string; instrument: string; base_lot: number; sl?: number; tp?: number }) {
    return this.request<{ status: string; message: string; orders_executed: any[] }>('/api/clients/broadcast-trade', {
      method: 'POST',
      body: data,
    });
  }

  async emergencyHaltAll() {
    return this.request<{ status: string; message: string }>('/api/clients/emergency-halt-all', {
      method: 'POST',
    });
  }

  async toggleClientCopy(account_number: string, is_active: boolean) {
    return this.request<{ status: string; message: string }>('/api/clients/toggle-copy', {
      method: 'POST',
      body: { account_number, is_active },
    });
  }

  // Quantum AI Sniper Market Engine
  async getOHLCV(symbol: string = 'Volatility 100 Index', timeframe: string = 'H1', count: number = 60) {
    const params = new URLSearchParams({ symbol, timeframe, count: String(count) });
    return this.request<{
      symbol: string;
      timeframe: string;
      digits: number;
      current_price: number;
      spread: number;
      candles: Array<{
        time: string;
        timestamp: number;
        open: number;
        high: number;
        low: number;
        close: number;
        volume: number;
        is_bull: boolean;
      }>;
      order_blocks: Array<{
        type: string;
        top: number;
        bottom: number;
        strength: string;
        active: boolean;
      }>;
      fair_value_gaps: Array<{
        type: string;
        top: number;
        bottom: number;
        status: string;
      }>;
      ai_sniper_setup: {
        direction: string;
        confidence: number;
        swarm_consensus: string;
        entry: number;
        stop_loss: number;
        tp1: number;
        tp2: number;
        tp3: number;
        risk_reward: string;
        regime: string;
      };
    }>(`/api/market/ohlcv?${params}`);
  }

  // Vision
  async analyzeChart(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return this.request<VisionAnalysis>('/api/vision/analyze', {
      method: 'POST',
      body: formData,
      isFormData: true,
    });
  }

  // ── Autopilot ──────────────────────────────────────────────────────

  async getAutopilotStatus() {
    return this.request<AutopilotStatus>('/api/autopilot/status');
  }

  async getAutopilotConfig() {
    return this.request<AutopilotConfig>('/api/autopilot/config');
  }

  async updateAutopilotConfig(data: Partial<AutopilotConfigUpdate>) {
    return this.request<AutopilotConfig>('/api/autopilot/config', {
      method: 'PUT',
      body: data,
    });
  }

  async enableAutopilot() {
    return this.request<{ status: string; mode: string; message: string }>('/api/autopilot/enable', {
      method: 'POST',
    });
  }

  async disableAutopilot() {
    return this.request<{ status: string; message: string }>('/api/autopilot/disable', {
      method: 'POST',
    });
  }

  async killAutopilot() {
    return this.request<{ status: string; message: string }>('/api/autopilot/kill', {
      method: 'POST',
    });
  }

  async unlockLiveMode() {
    return this.request<{ status: string; message: string }>('/api/autopilot/unlock-live', {
      method: 'POST',
    });
  }

  async getAutopilotTradeLog(limit: number = 50, actionFilter?: string) {
    const params = new URLSearchParams({ limit: String(limit) });
    if (actionFilter) params.set('action_filter', actionFilter);
    return this.request<AutopilotTradeLog>(`/api/autopilot/trade-log?${params}`);
  }

  async getAutopilotPerformance() {
    return this.request<AutopilotPerformance>('/api/autopilot/performance');
  }
}

// Error class
export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

// Type definitions
export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  license_tier: string;
  license_status: string;
  created_at: string;
}

export interface LicenseInfo {
  tier: string;
  status: string;
  signals_used_today: number;
  signals_limit: number;
  expires_at: string | null;
}

// Security types
export interface SessionInfo {
  action: string;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

export interface ApiKeyCreated {
  id: string;
  name: string;
  raw_key: string;
  key_prefix: string;
  permissions: string[];
  created_at: string;
}

export interface ApiKeyInfo {
  id: string;
  name: string;
  key_prefix: string;
  permissions: string[];
  is_active: boolean;
  last_used_at: string | null;
  expires_at: string | null;
  created_at: string;
}

export interface AuditLogEntry {
  id: string;
  action: string;
  details: Record<string, unknown>;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

export interface DashboardSummary {
  total_pnl: number;
  total_trades: number;
  win_rate: number;
  ai_accuracy: number;
  open_trades: number;
  today_pnl: number;
  week_pnl: number;
  month_pnl: number;
  current_regime: string;
  active_models: string[];
  connection_status: string;
  live_balance?: number;
  live_equity?: number;
  account_number?: string;
  broker_name?: string;
  recovery_level?: string;
  recovery_multiplier?: number;
  auto_trade_enabled?: boolean;
}

export interface DrawdownInfo {
  current_drawdown_pct: number;
  current_drawdown_value: number;
  max_drawdown_pct: number;
  max_drawdown_value: number;
  guard_threshold: number;
  guard_active: boolean;
  guard_reason: string | null;
  risk_per_trade: number;
}

export interface PLBreakdown {
  by_instrument: Record<string, number>;
  by_session: Record<string, number>;
  by_model_category: Record<string, number>;
  by_day_of_week: Record<string, number>;
}

export interface Signal {
  id: string;
  instrument: string;
  timeframe: string;
  direction: string;
  confidence: number;
  regime: string;
  model_votes: Record<string, string>;
  model_confidences: Record<string, number>;
  entry_price: number | null;
  stop_loss: number | null;
  take_profit: number | null;
  created_at: string;
}

export interface SignalList {
  signals: Signal[];
  total: number;
}

export interface TradeCreate {
  instrument: string;
  direction: string;
  entry_price: number;
  lot_size?: number;
  signal_id?: string;
  confidence_at_entry?: number;
  model_votes_at_entry?: Record<string, string>;
}

export interface Trade {
  id: string;
  instrument: string;
  direction: string;
  entry_price: number;
  exit_price: number | null;
  lot_size: number;
  pnl: number;
  pnl_pips: number;
  status: string;
  confidence_at_entry: number | null;
  model_votes_at_entry: Record<string, string> | null;
  opened_at: string;
  closed_at: string | null;
}

export interface TradeList {
  trades: Trade[];
  total: number;
}

export interface TradeStats {
  total_trades: number;
  open_trades: number;
  closed_trades: number;
  total_pnl: number;
  win_rate: number;
  avg_pnl: number;
  best_trade: number;
  worst_trade: number;
  avg_confidence: number;
}

export interface VisionAnalysis {
  id: string;
  filename: string;
  asset_detected?: string;
  status: string;
  confidence: number;
  image_quality: string;
  detected_patterns: Array<{
    pattern: string;
    confidence: number;
    location?: string;
    significance?: string;
    price_level?: string;
    strength?: string;
    [key: string]: any;
  }>;
  summary: string;
  suggested_action: {
    asset?: string;
    direction: string;
    entry_zone: string;
    stop_loss: string;
    take_profit: string;
    take_profit_levels?: {
      tp1_conservative: string;
      tp2_standard: string;
      tp3_extended: string;
    };
    risk_reward?: string;
    confidence: number;
    setup_rating?: string;
  };
  disclaimer: string;
}

// ── Autopilot Types ──────────────────────────────────────────────────

export interface AutopilotStatus {
  is_running: boolean;
  mode: string;
  is_enabled: boolean;
  is_drift_paused: boolean;
  paper_trade_count: number;
  paper_trade_required: number;
  paper_progress_pct: number;
  can_unlock_live: boolean;
  total_decisions: number;
  recent_executed: number;
  recent_skipped: number;
  recent_paper: number;
  last_decision: Record<string, any> | null;
  last_5_decisions: Record<string, any>[];
  circuit_breakers: {
    daily_loss_breaker: boolean;
    weekly_loss_breaker: boolean;
    max_positions: boolean;
    drawdown_guard: boolean;
    news_blackout: boolean;
    performance_drift: boolean;
  } | null;
}

export interface AutopilotConfig {
  id: string;
  user_id: string;
  is_enabled: boolean;
  mode: string;
  confidence_threshold: number;
  risk_per_trade_pct: number;
  daily_max_loss_pct: number;
  weekly_max_loss_pct: number;
  max_concurrent_positions: number;
  scan_interval_seconds: number;
  instruments: string[];
  instrument_modes: Record<string, string>;
  news_blackout_enabled: boolean;
  paper_trade_count: number;
  paper_trade_required: number;
  performance_baseline_winrate: number;
  drift_threshold_pct: number;
  is_drift_paused: boolean;
  daily_loss_today: number;
  created_at: string;
  updated_at: string;
}

export interface AutopilotConfigUpdate {
  confidence_threshold?: number;
  risk_per_trade_pct?: number;
  daily_max_loss_pct?: number;
  weekly_max_loss_pct?: number;
  max_concurrent_positions?: number;
  scan_interval_seconds?: number;
  instruments?: string[];
  instrument_modes?: Record<string, string>;
  news_blackout_enabled?: boolean;
  paper_trade_required?: number;
  drift_threshold_pct?: number;
}

export interface AutopilotTradeLogEntry {
  instrument: string;
  timeframe: string;
  direction: string;
  confidence: number;
  action: string;
  reason: string;
  gate_results: Array<{ gate: string; passed: boolean; reason: string }>;
  lot_size: number;
  entry_price: number | null;
  stop_loss: number | null;
  take_profit: number | null;
  timestamp: string;
}

export interface AutopilotTradeLog {
  decisions: AutopilotTradeLogEntry[];
  total: number;
}

export interface AutopilotPerformance {
  live_winrate: number;
  baseline_winrate: number;
  drift_pct: number;
  drift_threshold_pct: number;
  is_drifted: boolean;
  total_paper_trades: number;
  total_live_trades: number;
  paper_profit: number;
  live_profit: number;
}

// Export singleton
export const api = new ApiClient(API_BASE);
export default api;

