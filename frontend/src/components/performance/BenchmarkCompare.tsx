import type { PerformanceSummary } from '@/types/portfolio'
import { formatBps, formatPercent } from '@/utils/formatters'
import Bar from './Bar'

interface BenchmarkCompareProps {
  summary: PerformanceSummary
  benchmarkName: string
}

/** Benchmark compare — portfolio total return vs its benchmark. */
export default function BenchmarkCompare({ summary, benchmarkName }: BenchmarkCompareProps) {
  const max = Math.max(
    Math.abs(summary.total_return_net_pct),
    Math.abs(summary.benchmark_return_pct),
    0.1,
  )
  const ahead = summary.active_return_bps >= 0
  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-100">Benchmark compare</h3>
        <span className={ahead ? 'badge-success' : 'badge-error'}>
          {ahead ? 'Ahead' : 'Behind'} by {formatBps(Math.abs(summary.active_return_bps))}
        </span>
      </div>
      <p className="text-xs text-gray-500 -mt-2">{benchmarkName}</p>
      <div className="space-y-2.5">
        <Bar
          label="Portfolio (net)"
          value={summary.total_return_net_pct}
          max={max}
          display={formatPercent(summary.total_return_net_pct)}
          tone={summary.total_return_net_pct >= 0 ? 'positive' : 'negative'}
        />
        <Bar
          label="Benchmark"
          value={summary.benchmark_return_pct}
          max={max}
          display={formatPercent(summary.benchmark_return_pct)}
          tone="neutral"
        />
      </div>
    </div>
  )
}
