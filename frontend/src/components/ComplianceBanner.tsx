import { AlertTriangle, CheckCircle2, ShieldAlert } from 'lucide-react'
import type { CompliantCommentary } from '@/types/commentary'

interface ComplianceBannerProps {
  commentary: CompliantCommentary
}

/** Surfaces compliance status, inserted disclaimers, and any rejections. */
export default function ComplianceBanner({ commentary }: ComplianceBannerProps) {
  const { compliance_status, rejections, inserted_disclaimers } = commentary

  if (compliance_status === 'rejected') {
    return (
      <div className="card border-red-800/50 bg-red-900/20">
        <div className="flex items-center gap-2 text-red-400 font-medium text-sm">
          <ShieldAlert size={16} /> Compliance rejected — resolve before delivery
        </div>
        <ul className="mt-2 space-y-1 text-xs text-red-300">
          {rejections.map((r, i) => (
            <li key={i}>• {r}</li>
          ))}
        </ul>
      </div>
    )
  }

  const isRewritten = compliance_status === 'rewritten'
  return (
    <div
      className={
        isRewritten
          ? 'card border-yellow-800/50 bg-yellow-900/10'
          : 'card border-green-800/50 bg-green-900/10'
      }
    >
      <div
        className={
          isRewritten
            ? 'flex items-center gap-2 text-yellow-400 font-medium text-sm'
            : 'flex items-center gap-2 text-green-400 font-medium text-sm'
        }
      >
        {isRewritten ? <AlertTriangle size={16} /> : <CheckCircle2 size={16} />}
        {isRewritten
          ? 'Passed with rewrites — review balancing notes'
          : 'Compliant — all claims substantiated'}
      </div>
      {inserted_disclaimers.length > 0 && (
        <div className="mt-2 text-xs text-gray-400">
          {inserted_disclaimers.length} approved disclaimer(s) inserted.
        </div>
      )}
    </div>
  )
}
