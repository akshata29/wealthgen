import { ShieldCheck, UserCheck } from 'lucide-react'
import type { ApprovalState } from '@/types/approvals'

interface ApprovalGateProps {
  approval: ApprovalState
  onApprove: (role: 'pm' | 'compliance') => void
  onDeliver: () => void
  disabled?: boolean
}

/** Amber human-in-the-loop gate: PM + Compliance sign-off before delivery. */
export default function ApprovalGate({
  approval,
  onApprove,
  onDeliver,
  disabled,
}: ApprovalGateProps) {
  const pmApproved = approval.pm_status === 'approved'
  const complianceApproved = approval.compliance_status === 'approved'
  const canDeliver = pmApproved && complianceApproved && !approval.delivered

  return (
    <div className="card border-yellow-800/50 bg-yellow-900/10 space-y-4">
      <div className="section-title text-yellow-500">Human-in-the-loop approval</div>

      <div className="grid grid-cols-2 gap-3">
        <button
          type="button"
          disabled={disabled || pmApproved}
          onClick={() => onApprove('pm')}
          className={pmApproved ? 'btn-secondary' : 'btn-primary'}
        >
          <span className="inline-flex items-center gap-2">
            <UserCheck size={15} />
            {pmApproved ? 'PM approved' : 'Approve as PM'}
          </span>
        </button>
        <button
          type="button"
          disabled={disabled || complianceApproved}
          onClick={() => onApprove('compliance')}
          className={complianceApproved ? 'btn-secondary' : 'btn-primary'}
        >
          <span className="inline-flex items-center gap-2">
            <ShieldCheck size={15} />
            {complianceApproved ? 'Compliance approved' : 'Approve as Compliance'}
          </span>
        </button>
      </div>

      <button
        type="button"
        disabled={!canDeliver}
        onClick={onDeliver}
        className="btn-primary w-full"
      >
        {approval.delivered ? 'Delivered' : 'Deliver commentary'}
      </button>
      {!canDeliver && !approval.delivered && (
        <p className="text-xs text-gray-500">
          Delivery is blocked until both PM and Compliance approve.
        </p>
      )}
    </div>
  )
}
