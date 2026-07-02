import { Link } from 'react-router-dom'
import { ChevronRight, Briefcase, Leaf, FileText } from 'lucide-react'
import type { ClientSummary } from '@/types/portfolio'

interface ClientCardProps {
  client: ClientSummary
  commentaryCount?: number
  pendingCount?: number
}

const RISK_BADGE: Record<string, string> = {
  conservative: 'badge-info',
  balanced: 'badge-accent',
  growth: 'badge-gold',
  aggressive: 'badge-error',
}

/** A client card showing risk profile, AUM, and their mandates. */
export default function ClientCard({ client, commentaryCount = 0, pendingCount = 0 }: ClientCardProps) {
  return (
    <div className="card space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-gray-100">{client.display_name}</h3>
            {client.esg_preference && <Leaf size={13} className="text-brand-teal" />}
          </div>
          <p className="text-xs text-gray-500">
            {client.segment} · {client.jurisdiction} · {client.advisor_id}
          </p>
        </div>
        <span className={RISK_BADGE[client.risk_profile] ?? 'badge'}>{client.risk_profile}</span>
      </div>

      <div className="flex items-center gap-4 text-xs text-gray-400">
        <span>AUM ${client.total_aum_musd.toFixed(1)}m</span>
        <span>Literacy: {client.financial_literacy}</span>
        <span>Tone: {client.tone_preference}</span>
      </div>

      {(commentaryCount > 0 || pendingCount > 0) && (
        <div className="flex items-center gap-2 text-xs">
          <span className="inline-flex items-center gap-1 text-gray-400">
            <FileText size={12} /> {commentaryCount} commentaries
          </span>
          {pendingCount > 0 && <span className="badge-warning">{pendingCount} pending</span>}
        </div>
      )}

      {client.life_event && (
        <div className="text-xs text-brand-gold">Life event: {client.life_event}</div>
      )}

      <div className="space-y-1.5 pt-1">
        {client.mandates.map((m) => (
          <Link
            key={m.mandate_id}
            to={`/portfolios/${m.mandate_id}`}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-50 hover:bg-border transition-colors group"
          >
            <Briefcase size={14} className="text-gray-500" />
            <div className="flex-1 min-w-0">
              <div className="text-sm text-gray-200 truncate">{m.display_name}</div>
              <div className="text-[11px] text-gray-500 truncate">
                {m.strategy} · ${m.aum_musd.toFixed(1)}m {m.base_currency}
              </div>
            </div>
            <ChevronRight size={14} className="text-gray-600 group-hover:text-gray-300" />
          </Link>
        ))}
      </div>
    </div>
  )
}
