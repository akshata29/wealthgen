// Mirrors backend app/models/commentary.py
export type Audience = 'client' | 'institutional' | 'ic'

export type SectionHeading =
  | 'Executive Summary'
  | 'Market Context'
  | 'Performance Attribution'
  | 'Positioning Changes'
  | 'House View & Outlook'
  | 'Risk & Compliance Note'
  | 'Next Steps'

export type ComplianceStatus = 'passed' | 'rewritten' | 'rejected'

export type CommentaryType =
  | 'ad_hoc'
  | 'quarterly_review'
  | 'annual_review'
  | 'event_driven'

export type ContextChannel =
  | 'advisor_portal'
  | 'fund_webpage'
  | 'market_commentary'
  | 'portfolio_manager'
  | 'research'
  | 'webcast'
  | 'email_alert'
  | 'wholesaler'

export interface AffectedHolding {
  ticker: string
  instrument: string
  weight: number
}

export interface LiveEvent {
  event: ContextSource
  affected_tickers: string[]
  affected_mandate_count: number
  total_mandates: number
  affected_mandates: {
    mandate_id: string
    display_name: string
    affected_holdings: AffectedHolding[]
  }[]
}

export interface ContextSource {
  source_id: string
  channel: ContextChannel
  publisher: string
  title: string
  summary: string
  url?: string | null
  published?: string | null
  periods: string[]
  themes: string[]
  commentary_types: string[]
  live: boolean
  key_points?: string[]
  affected_tickers?: string[]
  advisor_talking_point?: string | null
  affected_holdings?: AffectedHolding[]
}

export interface SourcedClaim {
  text: string
  value?: string | null
  source_id: string
  confidence?: number | null
}

export interface CommentarySection {
  heading: SectionHeading
  claims: SourcedClaim[]
}

export interface CommentaryDraft {
  mandate_id: string
  period: string
  audience: Audience
  sections: CommentarySection[]
  disclaimers: string[]
  source_map: Record<string, string>
  commentary_type?: CommentaryType
  context_sources?: ContextSource[]
}

export interface CompliantCommentary extends CommentaryDraft {
  id?: string
  compliance_status: ComplianceStatus
  inserted_disclaimers: string[]
  rejections: string[]
}

export interface GenerateCommentaryRequest {
  mandate_id: string
  period: string
  audience: Audience
  style?: NarrativeStyle | null
  commentary_type?: CommentaryType
  trigger?: BriefTrigger
  event_period?: string | null
  end_user_token?: string | null
}

export type Tone = 'warm' | 'neutral' | 'formal'
export type Literacy = 'novice' | 'informed' | 'expert'
export type BriefTrigger = 'scheduled' | 'ad_hoc' | 'event'

export interface NarrativeStyle {
  tone: Tone
  literacy: Literacy
  non_financial_language: boolean
}

export interface CommentarySummary {
  id: string
  mandate_id: string
  period: string
  audience: Audience
  commentary_type?: CommentaryType
  compliance_status: ComplianceStatus
  pm_status: string
  compliance_approval: string
  delivered: boolean
  updated_ts?: number | null
}
