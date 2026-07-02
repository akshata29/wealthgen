import type { PerformanceSummary } from '@/types/portfolio'
import { formatBps, formatPercent } from '@/utils/formatters'

interface StatGridProps {
  summary: PerformanceSummary
}

interface Stat {
  label: string
  value: string
  tone?: 'positive' | 'negative' | 'neutral'
}

function delta(value: number): 'positive' | 'negative' | 'neutral' {
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return 'neutral'
}

const TONE_TEXT = {
  positive: 'text-status-success',
  negative: 'text-status-error',
  neutral: 'text-gray-200',
}

/** Portfolio summary — the "how much" performance metrics at a glance. */
export default function StatGrid({ summary }: StatGridProps) {
  const stats: Stat[] = [
    { label: 'Total return (net)', value: formatPercent(summary.total_return_net_pct), tone: delta(summary.total_return_net_pct) },
    { label: 'Benchmark', value: formatPercent(summary.benchmark_return_pct), tone: delta(summary.benchmark_return_pct) },
    { label: 'Active return', value: formatBps(summary.active_return_bps), tone: delta(summary.active_return_bps) },
    { label: 'Tracking error', value: summary.tracking_error_pct != null ? `${summary.tracking_error_pct.toFixed(2)}%` : '—' },
    { label: 'Information ratio', value: summary.information_ratio != null ? summary.information_ratio.toFixed(2) : '—' },
    { label: 'Sharpe', value: summary.sharpe != null ? summary.sharpe.toFixed(2) : '—' },
    { label: 'Volatility (ex-ante)', value: summary.ex_ante_vol_pct != null ? `${summary.ex_ante_vol_pct.toFixed(2)}%` : '—' },
    { label: 'Max drawdown', value: summary.max_drawdown_pct != null ? formatPercent(summary.max_drawdown_pct) : '—', tone: 'negative' },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {stats.map((s) => (
        <div key={s.label} className="stat-card">
          <span className="stat-label">{s.label}</span>
          <span className={`stat-value ${s.tone ? TONE_TEXT[s.tone] : 'text-gray-100'}`}>
            {s.value}
          </span>
        </div>
      ))}
    </div>
  )
}
