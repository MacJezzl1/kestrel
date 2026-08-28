/**
 * Kestrel API Client
 * Centralized HTTP client for all backend API calls.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
  status: string;
  confidence: number;
  image_quality: string;
  detected_patterns: Array<{
    pattern: string;
    confidence: number;
    [key: string]: unknown;
  }>;
  summary: string;
  suggested_action: {
    direction: string;
    entry_zone: string;
    stop_loss: string;
    take_profit: string;
    confidence: number;
  };
  disclaimer: string;
}

// Export singleton
export const api = new ApiClient(API_BASE);
export default api;

