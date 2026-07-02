import { useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import PageHeader from '@/components/ui/PageHeader'
import CommentaryViewer from '@/components/CommentaryViewer'
import ComplianceBanner from '@/components/ComplianceBanner'
import ApprovalGate from '@/components/ApprovalGate'
import * as api from '@/utils/apiClient'
import type { ApprovalState } from '@/types/approvals'
import type { CompliantCommentary } from '@/types/commentary'

export default function ReviewApproval() {
  const { id } = useParams<{ id: string }>()
  const [params] = useSearchParams()
  const mandateId = params.get('mandate_id') ?? ''

  const [commentary, setCommentary] = useState<CompliantCommentary | null>(null)
  const [approval, setApproval] = useState<ApprovalState | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!id) return
    api
      .getCommentary(id, mandateId)
      .then((c) => {
        setCommentary(c)
        setApproval({
          commentary_id: c.id ?? id,
          pm_status: 'pending',
          compliance_status: 'pending',
          delivered: false,
        })
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Load failed'))
  }, [id, mandateId])

  async function handleApprove(role: 'pm' | 'compliance') {
    if (!id) return
    setBusy(true)
    setError(null)
    try {
      const res = await api.approveCommentary(id, mandateId, role, `${role}-001`)
      setApproval(res.approval)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Approval failed')
    } finally {
      setBusy(false)
    }
  }

  async function handleDeliver() {
    if (!id) return
    setBusy(true)
    setError(null)
    try {
      await api.deliverCommentary(id, mandateId)
      setApproval((a) => (a ? { ...a, delivered: true } : a))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delivery blocked')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <PageHeader title="Review & Approve" subtitle="Human-in-the-loop sign-off before delivery" />
      {error && <div className="badge-error">{error}</div>}
      {commentary && (
        <>
          <ComplianceBanner commentary={commentary} />
          {approval && (
            <ApprovalGate
              approval={approval}
              onApprove={handleApprove}
              onDeliver={handleDeliver}
              disabled={busy}
            />
          )}
          <CommentaryViewer commentary={commentary} />
        </>
      )}
    </div>
  )
}
