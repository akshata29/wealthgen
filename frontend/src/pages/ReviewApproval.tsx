import { useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { Pencil, ShieldCheck, Save, X } from 'lucide-react'
import PageHeader from '@/components/ui/PageHeader'
import CommentaryViewer from '@/components/CommentaryViewer'
import CommentaryEditor from '@/components/CommentaryEditor'
import ComplianceBanner from '@/components/ComplianceBanner'
import ApprovalGate from '@/components/ApprovalGate'
import * as api from '@/utils/apiClient'
import type { ApprovalState } from '@/types/approvals'
import type { CommentarySection, CompliantCommentary } from '@/types/commentary'

export default function ReviewApproval() {
  const { id } = useParams<{ id: string }>()
  const [params] = useSearchParams()
  const mandateId = params.get('mandate_id') ?? ''

  const [commentary, setCommentary] = useState<CompliantCommentary | null>(null)
  const [approval, setApproval] = useState<ApprovalState | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [editing, setEditing] = useState(false)
  const [draftSections, setDraftSections] = useState<CommentarySection[]>([])
  const [notice, setNotice] = useState<string | null>(null)

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

  function startEdit() {
    if (!commentary) return
    setDraftSections(structuredClone(commentary.sections))
    setEditing(true)
    setNotice(null)
  }

  async function saveEdits() {
    if (!id || !commentary) return
    setBusy(true)
    setError(null)
    try {
      await api.reviewCommentary(id, mandateId, 'advisor-001', draftSections, 'changes_requested')
      setCommentary({ ...commentary, sections: draftSections })
      setEditing(false)
      setNotice('Changes saved. Re-run compliance to re-check the edited draft.')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Save failed')
    } finally {
      setBusy(false)
    }
  }

  async function handleRerunCompliance() {
    if (!id) return
    setBusy(true)
    setError(null)
    try {
      const updated = await api.rerunCompliance(id, mandateId)
      setCommentary(updated)
      // Content changed -> approvals reset to pending.
      setApproval({
        commentary_id: updated.id ?? id,
        pm_status: 'pending',
        compliance_status: 'pending',
        delivered: false,
      })
      setNotice(
        updated.compliance_status === 'rejected'
          ? 'Still rejected — edit the flagged wording and re-run again.'
          : `Compliance re-checked: ${updated.compliance_status}.`,
      )
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Re-run failed')
    } finally {
      setBusy(false)
    }
  }

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

          <div className="card flex flex-wrap items-center gap-2">
            <span className="section-title !mb-0 mr-1">Editor</span>
            {!editing ? (
              <button className="btn-secondary" disabled={busy} onClick={startEdit}>
                <span className="inline-flex items-center gap-2">
                  <Pencil size={14} /> Edit draft
                </span>
              </button>
            ) : (
              <>
                <button className="btn-primary" disabled={busy} onClick={saveEdits}>
                  <span className="inline-flex items-center gap-2">
                    <Save size={14} /> Save changes
                  </span>
                </button>
                <button
                  className="btn-secondary"
                  disabled={busy}
                  onClick={() => {
                    setEditing(false)
                    setNotice(null)
                  }}
                >
                  <span className="inline-flex items-center gap-2">
                    <X size={14} /> Cancel
                  </span>
                </button>
              </>
            )}
            <button className="btn-secondary" disabled={busy || editing} onClick={handleRerunCompliance}>
              <span className="inline-flex items-center gap-2">
                <ShieldCheck size={14} /> Re-run compliance
              </span>
            </button>
            {notice && <span className="text-xs text-gray-400 basis-full">{notice}</span>}
          </div>

          {approval && !editing && (
            <ApprovalGate
              approval={approval}
              onApprove={handleApprove}
              onDeliver={handleDeliver}
              disabled={busy}
            />
          )}

          {editing ? (
            <CommentaryEditor sections={draftSections} onChange={setDraftSections} />
          ) : (
            <CommentaryViewer commentary={commentary} />
          )}
        </>
      )}
    </div>
  )
}
