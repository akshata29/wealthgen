import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import PageHeader from '@/components/ui/PageHeader'
import * as api from '@/utils/apiClient'
import { deriveCommentaryStatus, isActionable } from '@/utils/commentaryStatus'
import type { CommentarySummary } from '@/types/commentary'

type Filter = 'all' | 'pending' | 'approved' | 'delivered'

const FILTERS: { value: Filter; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'pending', label: 'Needs action' },
  { value: 'approved', label: 'Approved' },
  { value: 'delivered', label: 'Delivered' },
]

interface MandateInfo {
  mandateName: string
  clientName: string
}

export default function ReviewQueue() {
  const [items, setItems] = useState<CommentarySummary[]>([])
  const [mandateInfo, setMandateInfo] = useState<Record<string, MandateInfo>>({})
  const [filter, setFilter] = useState<Filter>('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    async function load() {
      try {
        const [all, clients] = await Promise.all([api.listAllCommentary(), api.getClients()])
        if (!active) return
        const info: Record<string, MandateInfo> = {}
        clients.forEach((c) =>
          c.mandates.forEach((m) => {
            info[m.mandate_id] = { mandateName: m.display_name, clientName: c.display_name }
          }),
        )
        setMandateInfo(info)
        setItems(all)
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : 'Failed to load review queue')
      } finally {
        if (active) setLoading(false)
      }
    }
    load()
    return () => {
      active = false
    }
  }, [])

  const filtered = useMemo(() => {
    switch (filter) {
      case 'pending':
        return items.filter(isActionable)
      case 'approved':
        return items.filter((c) => !c.delivered && c.pm_status === 'approved' && c.compliance_approval === 'approved')
      case 'delivered':
        return items.filter((c) => c.delivered)
      default:
        return items
    }
  }, [items, filter])

  const pendingCount = items.filter(isActionable).length

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <PageHeader
        title="Review queue"
        subtitle={
          loading ? 'Loading…' : `${items.length} commentaries · ${pendingCount} need action`
        }
      />

      <div className="inline-flex rounded-lg border border-border bg-surface-50 p-0.5">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={
              filter === f.value
                ? 'px-3 py-1.5 rounded-md text-sm font-medium bg-accent text-white'
                : 'px-3 py-1.5 rounded-md text-sm font-medium text-gray-400 hover:text-gray-100'
            }
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && <div className="badge-error">{error}</div>}
      {!error && !loading && filtered.length === 0 && (
        <p className="text-sm text-gray-500">Nothing here for this filter.</p>
      )}

      <div className="card divide-y divide-border p-0 overflow-hidden">
        {filtered.map((c) => {
          const s = deriveCommentaryStatus(c)
          const info = mandateInfo[c.mandate_id]
          return (
            <Link
              key={c.id}
              to={`/review/${c.id}?mandate_id=${encodeURIComponent(c.mandate_id)}`}
              className="flex items-center gap-3 px-4 py-3 hover:bg-surface-50 transition-colors group"
            >
              <div className="flex-1 min-w-0">
                <div className="text-sm text-gray-100 truncate">
                  {info?.clientName ?? c.mandate_id}
                  <span className="text-gray-500"> · {info?.mandateName ?? ''}</span>
                </div>
                <div className="text-[11px] text-gray-500">
                  {c.period} · {c.audience}
                  {c.updated_ts && ` · ${new Date(c.updated_ts * 1000).toLocaleDateString()}`}
                </div>
              </div>
              {c.compliance_status !== 'passed' && (
                <span className="badge-accent">{c.compliance_status}</span>
              )}
              <span className={s.badge}>{s.label}</span>
              <ChevronRight size={14} className="text-gray-600 group-hover:text-gray-300" />
            </Link>
          )
        })}
      </div>
    </div>
  )
}
