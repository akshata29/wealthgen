import type { CommentarySummary } from '@/types/commentary'

export interface DerivedStatus {
  label: string
  badge: string
}

/** Map a commentary's approval/compliance state to a display label + badge class. */
export function deriveCommentaryStatus(c: CommentarySummary): DerivedStatus {
  if (c.delivered) return { label: 'Delivered', badge: 'badge-success' }
  if (c.pm_status === 'approved' && c.compliance_approval === 'approved') {
    return { label: 'Approved · ready to deliver', badge: 'badge-info' }
  }
  if (c.pm_status === 'changes_requested' || c.compliance_approval === 'changes_requested') {
    return { label: 'Changes requested', badge: 'badge-warning' }
  }
  return { label: 'Pending review', badge: 'badge-warning' }
}

/** A commentary still needs advisor/compliance action until it is delivered. */
export function isActionable(c: CommentarySummary): boolean {
  return !c.delivered
}
