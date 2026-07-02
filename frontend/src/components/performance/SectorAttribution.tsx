import type { SectorComparison } from '@/types/portfolio'
import { formatBps } from '@/utils/formatters'
import Bar from './Bar'

interface SectorAttributionProps {
  contributors: SectorComparison[]
  detractors: SectorComparison[]
}

/** Sector compare — top contributors and detractors by Brinson total effect. */
export default function SectorAttribution({ contributors, detractors }: SectorAttributionProps) {
  const all = [...contributors, ...detractors]
  const max = Math.max(...all.map((s) => Math.abs(s.total_effect_bps)), 1)

  return (
    <div className="card space-y-4">
      <h3 className="text-sm font-semibold text-gray-100">Sector compare (attribution)</h3>

      <div>
        <div className="section-title !mb-2">Top contributors</div>
        <div className="space-y-2">
          {contributors.length === 0 && <p className="text-xs text-gray-500">None this period.</p>}
          {contributors.map((s) => (
            <Bar
              key={s.segment}
              label={s.segment}
              value={s.total_effect_bps}
              max={max}
              display={formatBps(s.total_effect_bps)}
              tone="positive"
            />
          ))}
        </div>
      </div>

      <div>
        <div className="section-title !mb-2">Top detractors</div>
        <div className="space-y-2">
          {detractors.length === 0 && <p className="text-xs text-gray-500">None this period.</p>}
          {detractors.map((s) => (
            <Bar
              key={s.segment}
              label={s.segment}
              value={s.total_effect_bps}
              max={max}
              display={formatBps(s.total_effect_bps)}
              tone="negative"
            />
          ))}
        </div>
      </div>
    </div>
  )
}
