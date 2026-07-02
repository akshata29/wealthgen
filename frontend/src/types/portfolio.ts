// Mirrors backend app/models/portfolio.py

export type RiskProfile = 'conservative' | 'balanced' | 'growth' | 'aggressive'
export type FinancialLiteracy = 'novice' | 'informed' | 'expert'
export type TonePreference = 'warm' | 'neutral' | 'formal'

export interface Mandate {
  mandate_id: string
  display_name: string
  client_id: string
  strategy: string
  benchmark_id: string
  benchmark_name?: string | null
  base_currency: string
  inception: string
  aum_musd: number
}

export interface Client {
  client_id: string
  display_name: string
  advisor_id: string
  jurisdiction: string
  risk_profile: RiskProfile
  financial_literacy: FinancialLiteracy
  tone_preference: TonePreference
  segment: string
  life_event?: string | null
  esg_preference: boolean
}

export interface ClientSummary extends Client {
  mandates: Mandate[]
  total_aum_musd: number
}

export interface PerformanceSummary {
  mandate_id: string
  period: string
  total_return_net_pct: number
  benchmark_return_pct: number
  active_return_bps: number
  tracking_error_pct?: number | null
  information_ratio?: number | null
  ex_ante_vol_pct?: number | null
  sharpe?: number | null
  max_drawdown_pct?: number | null
}

export interface SectorComparison {
  segment: string
  portfolio_weight: number
  benchmark_weight: number
  portfolio_return: number
  benchmark_return: number
  total_effect_bps: number
  source_id: string
}

export interface IndexReturn {
  index_name: string
  period_return_pct: number
  source_id: string
}

export interface PositioningChange {
  mandate_id: string
  period: string
  description: string
  direction: string
  magnitude?: string | null
  rationale?: string | null
  source_id: string
}

export interface PerformanceReport {
  mandate: Mandate
  period: string
  summary: PerformanceSummary
  benchmark_name: string
  top_contributors: SectorComparison[]
  top_detractors: SectorComparison[]
  index_returns: IndexReturn[]
  positioning_changes: PositioningChange[]
}

export interface Holding {
  mandate_id: string
  period: string
  ticker: string
  instrument: string
  isin: string
  asset_class: string
  sector: string
  region: string
  weight: number
  market_value_usd: number
  period_return_pct: number
}

export interface VixEvent {
  period: string
  vix_close: number
  event_trigger: boolean
  regime: string
  headline: string
}

export interface NextBestAction {
  title: string
  rationale: string
  risk_warning: string
  trigger_type: 'life_event' | 'market_event'
  source: string
}

export interface PeriodsResponse {
  periods: string[]
  latest: string
}

export interface Citation {
  source_id: string
  display: string
  url?: string | null
}

export interface ResearchResponse {
  answer: string
  citations: Citation[]
}
