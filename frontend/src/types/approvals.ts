// Mirrors backend app/models/approvals.py
export type ApprovalStatus = 'pending' | 'approved' | 'changes_requested'

export interface ApprovalState {
  commentary_id: string
  pm_status: ApprovalStatus
  compliance_status: ApprovalStatus
  delivered: boolean
}
