import { Radio, Sparkles, ExternalLink } from 'lucide-react'
import type { LiveEvent } from '@/types/commentary'

interface LiveEventBannerProps {
  item: LiveEvent
  onGenerateBrief?: (mandateId: string | null) => void
}

/** Indigo banner for a LIVE market event (Web IQ), cross-referenced to holdings. */
export default function LiveEventBanner({ item, onGenerateBrief }: LiveEventBannerProps) {
  const { event, affected_tickers, affected_mandate_count, total_mandates, affected_mandates } = item
  const firstMandate = affected_mandates[0]?.mandate_id ?? null

  return (
    <div className="rounded-xl border border-accent/40 bg-accent/10 p-4 flex items-start gap-3">
      <Radio size={18} className="text-accent mt-0.5 shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-semibold text-gray-100">Live market event</span>
          <span className="badge-accent">Web IQ · live</span>
          <span className="text-xs text-gray-400">{event.publisher}</span>
          {event.published && <span className="text-[11px] text-gray-500">{event.published}</span>}
        </div>
        <div className="text-sm text-gray-100 mt-1">{event.title}</div>
        <p className="text-xs text-gray-300 mt-1">{event.summary}</p>

        {affected_mandate_count > 0 ? (
          <div className="mt-2 flex items-center gap-1.5 flex-wrap">
            <span className="badge-warning text-[11px]">
              Affects {affected_mandate_count} of your {total_mandates} portfolios
            </span>
            {affected_tickers.map((t) => (
              <span key={t} className="badge-accent text-[11px]">
                {t}
              </span>
            ))}
          </div>
        ) : (
          <div className="mt-2 text-[11px] text-gray-500">
            No direct holdings impact detected in your portfolios.
          </div>
        )}

        {event.url && (
          <a
            href={event.url}
            target="_blank"
            rel="noreferrer"
            className="mt-1 inline-flex items-center gap-1 text-xs text-accent hover:underline"
          >
            <ExternalLink size={12} /> Open source
          </a>
        )}
      </div>
      {onGenerateBrief && affected_mandate_count > 0 && (
        <button className="btn-primary shrink-0" onClick={() => onGenerateBrief(firstMandate)}>
          <span className="inline-flex items-center gap-2">
            <Sparkles size={14} /> Event brief
          </span>
        </button>
      )}
    </div>
  )
}
