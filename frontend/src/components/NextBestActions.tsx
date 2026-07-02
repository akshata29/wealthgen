import { Lightbulb, User, TrendingDown } from 'lucide-react'
import type { NextBestAction } from '@/types/portfolio'

interface NextBestActionsProps {
  actions: NextBestAction[]
}

/** Next-best-action panel — compliant, human-gated suggestions. */
export default function NextBestActions({ actions }: NextBestActionsProps) {
  if (actions.length === 0) return null
  return (
    <div className="card space-y-3">
      <div className="flex items-center gap-2">
        <Lightbulb size={16} className="text-brand-gold" />
        <h3 className="text-sm font-semibold text-gray-100">Next best actions</h3>
        <span className="badge-warning ml-auto">Requires approval</span>
      </div>
      <div className="space-y-2.5">
        {actions.map((a) => (
          <div key={a.title} className="rounded-lg border border-border bg-surface-50 p-3 space-y-1.5">
            <div className="flex items-center gap-2">
              {a.trigger_type === 'life_event' ? (
                <User size={13} className="text-accent-hover" />
              ) : (
                <TrendingDown size={13} className="text-status-error" />
              )}
              <span className="text-sm font-medium text-gray-100">{a.title}</span>
            </div>
            <p className="text-xs text-gray-400">{a.rationale}</p>
            <p className="text-[11px] text-gray-500">{a.source}</p>
            <p className="text-[11px] text-yellow-500/80">⚠ {a.risk_warning}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
