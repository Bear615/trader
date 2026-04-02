export interface PricePoint {
  id: number
  timestamp: string
  price: number
  price_yesterday: number | null
  volume_usd: number | null
}

export interface Portfolio {
  id: number
  usd_balance: number
  xrp_balance: number
  starting_budget: number
  total_value_usd: number | null
  roi_pct: number | null
  created_at: string
  updated_at: string
}

export interface Trade {
  id: number
  timestamp: string
  action: 'BUY' | 'SELL'
  xrp_amount: number
  usd_amount: number
  price_at_trade: number
  fee_usd: number
  fee_type: 'maker' | 'taker'
  usd_balance_after: number
  xrp_balance_after: number
  ai_decision_id: number | null
  triggered_by: 'ai' | 'manual'
  pnl: number | null
  note: string | null
}

export interface AIDecision {
  id: number
  timestamp: string
  action: 'BUY' | 'SELL' | 'HOLD'
  xrp_amount: number | null
  confidence: number
  reasoning: string | null
  raw_prompt: string | null
  raw_response: string | null
  executed: boolean
  execution_error: string | null
  model_used: string | null
  prompt_tokens: number | null
  completion_tokens: number | null
}

export interface Metrics {
  total_value_usd: number
  roi_pct: number
  total_trades: number
  buy_count: number
  sell_count: number
  win_rate_pct: number
  avg_buy_price: number | null
  total_fees_usd: number
  xrp_balance: number
  usd_balance: number
  starting_budget: number
  current_price: number
}

export interface BacktestRun {
  id: number
  created_at: string
  status: 'pending' | 'running' | 'done' | 'error'
  start_date: string
  end_date: string
  initial_capital: number
  maker_fee_pct: number
  taker_fee_pct: number
  decisions_per_hour: number
  ai_price_window: number
  ai_model: string | null
  result: BacktestResult | null
  error_message: string | null
}

export interface BacktestResult {
  initial_capital: number
  final_value: number
  total_return_pct: number
  sharpe_ratio: number
  max_drawdown_pct: number
  win_rate_pct: number
  total_trades: number
  buy_count: number
  sell_count: number
  equity_curve: Array<{ timestamp: string; value: number }>
  trades: Trade[]
}

export interface SettingMeta {
  key: string
  default: unknown
  description: string
}

export interface SettingsResponse {
  settings: Record<string, unknown>
  meta: Record<string, SettingMeta>
}

export interface PaginatedResponse<T> {
  total: number
  page: number
  per_page: number
  items: T[]
}
