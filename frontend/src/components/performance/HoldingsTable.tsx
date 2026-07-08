import type { Holding } from '@/types/portfolio'
import { formatPercent } from '@/utils/formatters'

interface HoldingsTableProps {
  holdings: Holding[]
}

/** Portfolio holdings — the real fund building blocks, by weight. */
export default function HoldingsTable({ holdings }: HoldingsTableProps) {
  const rows = [...holdings].sort((a, b) => b.weight - a.weight)

  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-100">Holdings</h3>
        <span className="text-xs text-gray-500">{rows.length} funds</span>
      </div>

      {rows.length === 0 ? (
        <p className="text-xs text-gray-500">No holdings for this period.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-500 border-b border-border">
                <th className="py-2 pr-3 font-medium">Fund</th>
                <th className="py-2 px-3 font-medium">Sleeve</th>
                <th className="py-2 px-3 font-medium">Region</th>
                <th className="py-2 px-3 font-medium text-right">Weight</th>
                <th className="py-2 pl-3 font-medium text-right">Return</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((h) => (
                <tr key={h.ticker} className="border-b border-border/50 last:border-0">
                  <td className="py-2 pr-3">
                    <div className="flex items-center gap-2">
                      <span className="badge-accent text-[11px]">{h.ticker}</span>
                      <span className="text-gray-200">{h.instrument}</span>
                    </div>
                  </td>
                  <td className="py-2 px-3 text-gray-400">{h.sector}</td>
                  <td className="py-2 px-3 text-gray-400">{h.region}</td>
                  <td className="py-2 px-3 text-right text-gray-200 tabular-nums">
                    {(h.weight * 100).toFixed(1)}%
                  </td>
                  <td
                    className={
                      'py-2 pl-3 text-right tabular-nums ' +
                      (h.period_return_pct >= 0 ? 'text-green-400' : 'text-red-400')
                    }
                  >
                    {formatPercent(h.period_return_pct)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
