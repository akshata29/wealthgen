import type { IndexReturn } from '@/types/portfolio'
import { formatPercent } from '@/utils/formatters'
import Bar from './Bar'

interface IndexCompareProps {
  indexReturns: IndexReturn[]
  portfolioReturn: number
}

/** Index / ETF compare — market index returns alongside the portfolio. */
export default function IndexCompare({ indexReturns, portfolioReturn }: IndexCompareProps) {
  const rows = [
    { index_name: 'This portfolio', period_return_pct: portfolioReturn, source_id: 'portfolio' },
    ...indexReturns,
  ]
  const max = Math.max(...rows.map((r) => Math.abs(r.period_return_pct)), 0.1)

  return (
    <div className="card space-y-4">
      <h3 className="text-sm font-semibold text-gray-100">Index / ETF compare</h3>
      <div className="space-y-2.5">
        {rows.map((r) => (
          <Bar
            key={r.source_id}
            label={r.index_name}
            value={r.period_return_pct}
            max={max}
            display={formatPercent(r.period_return_pct, 1)}
            tone={
              r.source_id === 'portfolio'
                ? 'accent'
                : r.period_return_pct >= 0
                  ? 'positive'
                  : 'negative'
            }
          />
        ))}
      </div>
    </div>
  )
}
