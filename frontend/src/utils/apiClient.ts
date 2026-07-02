// Typed API client for the WealthGen backend. Vite proxies /api to FastAPI.
import type { ApprovalState } from '@/types/approvals'
import type {
  CommentarySection,
  CommentarySummary,
  CompliantCommentary,
  GenerateCommentaryRequest,
} from '@/types/commentary'
import type {
  ClientSummary,
  Holding,
  Mandate,
  NextBestAction,
  PeriodsResponse,
  PerformanceReport,
  ResearchResponse,
  VixEvent,
} from '@/types/portfolio'

const BASE = '/api'

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail: unknown
    try {
      detail = (await res.json())?.detail
    } catch {
      detail = res.statusText
    }
    const message =
      typeof detail === 'object' && detail !== null && 'message' in detail
        ? String((detail as { message: unknown }).message)
        : JSON.stringify(detail)
    throw new Error(message)
  }
  return res.json() as Promise<T>
}

export interface SettingsInfo {
  jurisdictions: string[]
  default_audience: string
  endpoints: Record<string, boolean>
}

export interface IngestResult {
  mandate_id: string
  facts_indexed: number
  needs_review: string[]
}

export async function getSettings(): Promise<SettingsInfo> {
  return handle(await fetch(`${BASE}/settings`))
}

export async function ingestPdfs(
  mandateId: string,
  advisorId: string,
  clientId: string,
  sessionId: string,
  files: File[],
): Promise<IngestResult> {
  const form = new FormData()
  form.append('mandate_id', mandateId)
  form.append('advisor_id', advisorId)
  form.append('client_id', clientId)
  form.append('session_id', sessionId)
  files.forEach((f) => form.append('files', f))
  return handle(await fetch(`${BASE}/ingest`, { method: 'POST', body: form }))
}

export async function generateCommentary(
  req: GenerateCommentaryRequest,
): Promise<CompliantCommentary> {
  return handle(
    await fetch(`${BASE}/commentary/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }),
  )
}

export async function getCommentary(
  id: string,
  mandateId: string,
): Promise<CompliantCommentary> {
  return handle(
    await fetch(`${BASE}/commentary/${id}?mandate_id=${encodeURIComponent(mandateId)}`),
  )
}

export async function listCommentary(mandateId: string): Promise<CommentarySummary[]> {
  return handle(await fetch(`${BASE}/commentary?mandate_id=${encodeURIComponent(mandateId)}`))
}

export async function listAllCommentary(): Promise<CommentarySummary[]> {
  return handle(await fetch(`${BASE}/commentary/all`))
}

export async function reviewCommentary(
  id: string,
  mandateId: string,
  advisorId: string,
  sections?: CommentarySection[],
  pmStatus?: string,
): Promise<{ commentary_id: string; status: string }> {
  return handle(
    await fetch(
      `${BASE}/commentary/${id}/review?mandate_id=${encodeURIComponent(mandateId)}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sections, pm_status: pmStatus, advisor_id: advisorId }),
      },
    ),
  )
}

export async function approveCommentary(
  id: string,
  mandateId: string,
  role: 'pm' | 'compliance',
  approverId: string,
): Promise<{ commentary_id: string; approval: ApprovalState }> {
  return handle(
    await fetch(
      `${BASE}/commentary/${id}/approve?mandate_id=${encodeURIComponent(mandateId)}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role, approver_id: approverId }),
      },
    ),
  )
}

export async function deliverCommentary(
  id: string,
  mandateId: string,
): Promise<{ commentary_id: string; status: string }> {
  return handle(
    await fetch(
      `${BASE}/commentary/${id}/deliver?mandate_id=${encodeURIComponent(mandateId)}`,
      { method: 'POST' },
    ),
  )
}

// --- Advisory workspace: clients, portfolios, performance, events ---

export async function getPeriods(): Promise<PeriodsResponse> {
  return handle(await fetch(`${BASE}/periods`))
}

export async function getClients(): Promise<ClientSummary[]> {
  return handle(await fetch(`${BASE}/clients`))
}

export async function getClient(clientId: string): Promise<ClientSummary> {
  return handle(await fetch(`${BASE}/clients/${encodeURIComponent(clientId)}`))
}

export async function getMandate(mandateId: string): Promise<Mandate> {
  return handle(await fetch(`${BASE}/mandates/${encodeURIComponent(mandateId)}`))
}

function periodQuery(period?: string): string {
  return period ? `?period=${encodeURIComponent(period)}` : ''
}

export async function getPerformance(
  mandateId: string,
  period?: string,
): Promise<PerformanceReport> {
  return handle(
    await fetch(`${BASE}/mandates/${encodeURIComponent(mandateId)}/performance${periodQuery(period)}`),
  )
}

export async function getHoldings(mandateId: string, period?: string): Promise<Holding[]> {
  return handle(
    await fetch(`${BASE}/mandates/${encodeURIComponent(mandateId)}/holdings${periodQuery(period)}`),
  )
}

export async function getNextBestActions(
  mandateId: string,
  period?: string,
): Promise<NextBestAction[]> {
  return handle(
    await fetch(
      `${BASE}/mandates/${encodeURIComponent(mandateId)}/next-best-actions${periodQuery(period)}`,
    ),
  )
}

export async function getVixEvents(triggersOnly = false): Promise<VixEvent[]> {
  return handle(await fetch(`${BASE}/events/vix?triggers_only=${triggersOnly}`))
}

// --- Research (MCP: Morningstar / LSEG) ---

export async function getResearchProviders(): Promise<{ providers: string[] }> {
  return handle(await fetch(`${BASE}/research/providers`))
}

export async function getMorningstarXray(
  mandateId: string,
  period?: string,
): Promise<ResearchResponse> {
  return handle(
    await fetch(
      `${BASE}/mandates/${encodeURIComponent(mandateId)}/morningstar-xray${periodQuery(period)}`,
    ),
  )
}

export async function getLsegContext(
  mandateId: string,
  period?: string,
): Promise<ResearchResponse> {
  return handle(
    await fetch(
      `${BASE}/mandates/${encodeURIComponent(mandateId)}/lseg-context${periodQuery(period)}`,
    ),
  )
}

export async function researchQuery(query: string): Promise<ResearchResponse> {
  return handle(
    await fetch(`${BASE}/research/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    }),
  )
}

// --- Export ---

export function exportUrl(
  id: string,
  mandateId: string,
  format: 'pdf' | 'docx',
): string {
  return `${BASE}/commentary/${id}/export/${format}?mandate_id=${encodeURIComponent(mandateId)}`
}

export function emailExportUrl(id: string, mandateId: string, to: string): string {
  return `${BASE}/commentary/${id}/export/email?mandate_id=${encodeURIComponent(
    mandateId,
  )}&to=${encodeURIComponent(to)}`
}
