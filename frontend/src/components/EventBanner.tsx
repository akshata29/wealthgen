import { AlertTriangle, Sparkles } from 'lucide-react'
import type { VixEvent } from '@/types/portfolio'

interface EventBannerProps {
  event: VixEvent
  onGenerateBrief?: () => void
}

/** Amber event banner for a triggered market event (e.g. VIX spike). */
export default function EventBanner({ event, onGenerateBrief }: EventBannerProps) {
  return (
    <div className="rounded-xl border border-yellow-700/40 bg-yellow-900/20 p-4 flex items-start gap-3">
      <AlertTriangle size={18} className="text-brand-gold mt-0.5 shrink-0" />
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-yellow-300">
            Market event — {event.period}
          </span>
          <span className="badge-gold">VIX {event.vix_close.toFixed(0)} · {event.regime}</span>
        </div>
        <p className="text-xs text-gray-300 mt-1">{event.headline}</p>
      </div>
      {onGenerateBrief && (
        <button className="btn-primary shrink-0" onClick={onGenerateBrief}>
          <span className="inline-flex items-center gap-2">
            <Sparkles size={14} />
            Event brief
          </span>
        </button>
      )}
    </div>
  )
}
