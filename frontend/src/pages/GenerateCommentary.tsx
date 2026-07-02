import { useState } from 'react'
import { Sparkles } from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import PageHeader from '@/components/ui/PageHeader'
import PdfUpload from '@/components/PdfUpload'
import AudienceSelector from '@/components/AudienceSelector'
import CommentaryViewer from '@/components/CommentaryViewer'
import ComplianceBanner from '@/components/ComplianceBanner'
import ToneControls from '@/components/ToneControls'
import ExportMenu from '@/components/ExportMenu'
import * as api from '@/utils/apiClient'
import type {
  Audience,
  BriefTrigger,
  CompliantCommentary,
  NarrativeStyle,
} from '@/types/commentary'

export default function GenerateCommentary() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [mandateId, setMandateId] = useState(
    params.get('mandate_id') ?? 'northbridge-global-balanced',
  )
  const [period, setPeriod] = useState(params.get('period') ?? 'Q2-2026')
  const [audience, setAudience] = useState<Audience>('client')
  const [style, setStyle] = useState<NarrativeStyle>({
    tone: 'neutral',
    literacy: 'informed',
    non_financial_language: false,
  })
  const [trigger, setTrigger] = useState<BriefTrigger>(
    (params.get('trigger') as BriefTrigger) ?? 'scheduled',
  )
  const [files, setFiles] = useState<File[]>([])
  const [needsReview, setNeedsReview] = useState<string[]>([])
  const [commentary, setCommentary] = useState<CompliantCommentary | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleGenerate() {
    setBusy(true)
    setError(null)
    try {
      if (files.length > 0) {
        const ingest = await api.ingestPdfs(
          mandateId,
          'adv-001',
          mandateId,
          `sess-${Date.now()}`,
          files,
        )
        setNeedsReview(ingest.needs_review)
      }
      const result = await api.generateCommentary({
        mandate_id: mandateId,
        period,
        audience,
        style,
        trigger,
        event_period: trigger === 'event' ? period : null,
      })
      setCommentary(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Generation failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <PageHeader
        title="Generate Commentary"
        subtitle="Grounded, benchmark-aware, compliance-safe portfolio narrative"
        actions={<AudienceSelector value={audience} onChange={setAudience} />}
      />

      <div className="card space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <label className="block">
            <span className="section-title">Mandate</span>
            <input className="input" value={mandateId} onChange={(e) => setMandateId(e.target.value)} />
          </label>
          <label className="block">
            <span className="section-title">Reporting period</span>
            <input className="input" value={period} onChange={(e) => setPeriod(e.target.value)} />
          </label>
        </div>
        <PdfUpload onFilesSelected={setFiles} needsReview={needsReview} />
        <button className="btn-primary" disabled={busy} onClick={handleGenerate}>
          <span className="inline-flex items-center gap-2">
            <Sparkles size={15} />
            {busy ? 'Generating…' : 'Generate commentary'}
          </span>
        </button>
        {error && <div className="badge-error">{error}</div>}
      </div>

      <ToneControls
        style={style}
        onStyleChange={setStyle}
        trigger={trigger}
        onTriggerChange={setTrigger}
      />

      {commentary && (
        <div className="space-y-4">
          <ComplianceBanner commentary={commentary} />
          <CommentaryViewer commentary={commentary} />
          {commentary.id && <ExportMenu commentaryId={commentary.id} mandateId={mandateId} />}
          {commentary.id && (
            <button
              className="btn-secondary"
              onClick={() => navigate(`/review/${commentary.id}?mandate_id=${mandateId}`)}
            >
              Send to review &amp; approval
            </button>
          )}
        </div>
      )}
    </div>
  )
}
