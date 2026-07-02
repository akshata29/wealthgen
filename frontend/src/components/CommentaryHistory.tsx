import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { History, ChevronRight, CheckCircle2, Clock, AlertTriangle, Send } from 'lucide-react'
import * as api from '@/utils/apiClient'
import type { CommentarySummary } from '@/types/commentary'

interface CommentaryHistoryProps {
  mandateId: string
  /** Bump to force a refresh (e.g. after generating a new commentary). */
  refreshKey?: number
}

type Status = { label: string; badge: string; icon: JSX.Element }

function deriveStatus(c: CommentarySummary): Status {
  if (c.delivered) {
    return { label: 'Delivered', badge: 'badge-success', icon: <Send size={12} /> }
  }
  if (c.pm_status === 'approved' && c.compliance_approval === 'approved') {
    return { label: 'Approved · ready to deliver', badge: 'badge-info', icon: <CheckCircle2 size={12} /> }
  }
  if (c.pm_status === 'changes_requested' || c.compliance_approval === 'changes_requested') {
    return { label: 'Changes requested', badge: 'badge-warning', icon: <AlertTriangle size={12} /> }
  }
  return { label: 'Pending review', badge: 'badge-warning', icon: <Clock size={12} /> }
}

export default function CommentaryHistory({ mandateId, refreshKey = 0 }: CommentaryHistoryProps) {
  const [items, setItems] = useState<CommentarySummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    setLoading(true)
    api
      .listCommentary(mandateId)
      .then((rows) => active && (setItems(rows), setError(null)))
      .catch((e) => active && setError(e instanceof Error ? e.message : 'Failed to load history'))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [mandateId, refreshKey])

  return (
    <div className="card space-y-3">
      <div className="flex items-center gap-2">
        <History size={16} className="text-gray-400" />
        <h3 className="text-sm font-semibold text-gray-100">Commentary history</h3>
        {!loading && <span className="text-xs text-gray-500">({items.length})</span>}
      </div>

      {error && <div className="badge-error">{error}</div>}
      {!error && !loading && items.length === 0 && (
        <p className="text-xs text-gray-500">No commentary generated yet for this mandate.</p>
      )}

      <div className="space-y-1.5">
        {items.map((c) => {
          const s = deriveStatus(c)
          return (
            <Link
              key={c.id}
              to={`/review/${c.id}?mandate_id=${encodeURIComponent(mandateId)}`}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-surface-50 hover:bg-border transition-colors group"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-200">{c.period}</span>
                  <span className="text-[11px] text-gray-500 uppercase">{c.audience}</span>
                  {c.compliance_status !== 'passed' && (
                    <span className="badge-accent">{c.compliance_status}</span>
                  )}
                </div>
                {c.updated_ts && (
                  <div className="text-[11px] text-gray-500">
                    {new Date(c.updated_ts * 1000).toLocaleString()}
                  </div>
                )}
              </div>
              <span className={s.badge}>
                {s.icon}
                {s.label}
              </span>
              <ChevronRight size={14} className="text-gray-600 group-hover:text-gray-300" />
            </Link>
          )
        })}
      </div>
    </div>
  )
}
