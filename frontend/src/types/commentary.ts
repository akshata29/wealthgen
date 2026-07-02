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
  compliance_status: ComplianceStatus
  pm_status: string
  compliance_approval: string
  delivered: boolean
  updated_ts?: number | null
}
