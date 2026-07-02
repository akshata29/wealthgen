import { useState } from 'react'
import { Sparkles, ExternalLink } from 'lucide-react'
import * as api from '@/utils/apiClient'
import type { ResearchResponse } from '@/types/portfolio'

interface MorningstarXrayProps {
  mandateId: string
  period: string
}

/** On-demand Morningstar X-Ray via the research MCP tool (Foundry). */
export default function MorningstarXray({ mandateId, period }: MorningstarXrayProps) {
  const [data, setData] = useState<ResearchResponse | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setBusy(true)
    setError(null)
    try {
      setData(await api.getMorningstarXray(mandateId, period))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'X-Ray failed')
    } finally {
      setBusy(false)
    }
  }

  const notConfigured = error?.toLowerCase().includes('connection') || error?.toLowerCase().includes('configured')

  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-gray-100">Morningstar X-Ray</h3>
          <span className="badge-info">MCP</span>
        </div>
        <button className="btn-secondary" disabled={busy} onClick={run}>
          <span className="inline-flex items-center gap-2">
            <Sparkles size={14} />
            {busy ? 'Running…' : data ? 'Re-run' : 'Run X-Ray'}
          </span>
        </button>
      </div>

      <p className="text-xs text-gray-500 -mt-1">
        Independent asset allocation, sector, region, style, and risk/return analysis from
        Morningstar, based on this mandate&apos;s holdings.
      </p>

      {error && (
        <div className="space-y-1">
          <div className="badge-error">{error}</div>
          {notConfigured && (
            <p className="text-[11px] text-gray-500">
              Connect Morningstar in the Foundry project (Tools → add → authenticate) and set
              MORNINGSTAR_CONNECTION_NAME in the backend .env.
            </p>
          )}
        </div>
      )}

      {data && (
        <div className="space-y-3">
          <div className="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed">
            {data.answer}
          </div>
          {data.citations.length > 0 && (
            <div className="border-t border-border pt-2">
              <div className="section-title !mb-1.5">Sources</div>
              <div className="flex flex-wrap gap-1.5">
                {data.citations.map((c, i) => (
                  <a
                    key={`${c.source_id}-${i}`}
                    href={c.url ?? undefined}
                    target="_blank"
                    rel="noreferrer"
                    className="badge-accent"
                  >
                    {c.display}
                    {c.url && <ExternalLink size={10} />}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
