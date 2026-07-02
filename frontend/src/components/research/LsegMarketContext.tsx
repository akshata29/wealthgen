import { useState } from 'react'
import { LineChart, ExternalLink } from 'lucide-react'
import * as api from '@/utils/apiClient'
import type { ResearchResponse } from '@/types/portfolio'

interface LsegMarketContextProps {
  mandateId: string
  period: string
}

/** On-demand LSEG market context (indices, curve, FX, themes) via the research MCP tool. */
export default function LsegMarketContext({ mandateId, period }: LsegMarketContextProps) {
  const [data, setData] = useState<ResearchResponse | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setBusy(true)
    setError(null)
    try {
      setData(await api.getLsegContext(mandateId, period))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'LSEG context failed')
    } finally {
      setBusy(false)
    }
  }

  const notConfigured =
    error?.toLowerCase().includes('logged in') || error?.toLowerCase().includes('configured')

  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-gray-100">LSEG market context</h3>
          <span className="badge-info">MCP</span>
        </div>
        <button className="btn-secondary" disabled={busy} onClick={run}>
          <span className="inline-flex items-center gap-2">
            <LineChart size={14} />
            {busy ? 'Loading…' : data ? 'Refresh' : 'Load context'}
          </span>
        </button>
      </div>

      <p className="text-xs text-gray-500 -mt-1">
        Index returns, government yield-curve moves, FX, and macro themes for {period} from LSEG.
      </p>

      {error && (
        <div className="space-y-1">
          <div className="badge-error">{error}</div>
          {notConfigured && (
            <p className="text-[11px] text-gray-500">
              Run the one-time login: <code>python -m scripts.mcp_login lseg</code>
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
