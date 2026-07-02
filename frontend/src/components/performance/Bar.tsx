interface BarProps {
  label: string
  /** Value used for the bar width, relative to `max`. */
  value: number
  max: number
  /** Text shown at the end of the row. */
  display: string
  tone?: 'positive' | 'negative' | 'neutral' | 'accent'
}

const TONE_BG: Record<NonNullable<BarProps['tone']>, string> = {
  positive: 'bg-status-success',
  negative: 'bg-status-error',
  neutral: 'bg-gray-500',
  accent: 'bg-accent',
}

/** Lightweight horizontal bar (no chart library) for compare widgets. */
export default function Bar({ label, value, max, display, tone = 'accent' }: BarProps) {
  const pct = max > 0 ? Math.min(100, (Math.abs(value) / max) * 100) : 0
  return (
    <div className="flex items-center gap-3 text-sm">
      <div className="w-40 shrink-0 truncate text-gray-400" title={label}>
        {label}
      </div>
      <div className="flex-1 h-2.5 rounded-full bg-surface-50 overflow-hidden">
        <div className={`h-full rounded-full ${TONE_BG[tone]}`} style={{ width: `${pct}%` }} />
      </div>
      <div className="w-20 shrink-0 text-right font-medium text-gray-200 tabular-nums">
        {display}
      </div>
    </div>
  )
}
