import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import ApprovalGate from '../ApprovalGate'
import type { ApprovalState } from '@/types/approvals'

function renderGate(overrides: Partial<ApprovalState>) {
  const approval: ApprovalState = {
    commentary_id: 'c1',
    pm_status: 'pending',
    compliance_status: 'pending',
    delivered: false,
    ...overrides,
  }
  render(
    <ApprovalGate approval={approval} onApprove={vi.fn()} onDeliver={vi.fn()} />,
  )
}

describe('ApprovalGate', () => {
  it('disables delivery until both PM and Compliance approve', () => {
    renderGate({ pm_status: 'approved' })
    const deliver = screen.getByRole('button', { name: /deliver commentary/i })
    expect(deliver).toBeDisabled()
  })

  it('enables delivery when both approve', () => {
    renderGate({ pm_status: 'approved', compliance_status: 'approved' })
    const deliver = screen.getByRole('button', { name: /deliver commentary/i })
    expect(deliver).toBeEnabled()
  })
})
