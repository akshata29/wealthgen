import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import CommentaryViewer from '../CommentaryViewer'
import type { CompliantCommentary } from '@/types/commentary'

const commentary: CompliantCommentary = {
  mandate_id: 'm1',
  period: 'Q2-2026',
  audience: 'client',
  sections: [
    {
      heading: 'Performance Attribution',
      claims: [{ text: 'Asset allocation contributed', value: '+35 bps', source_id: 'attr:alloc' }],
    },
  ],
  disclaimers: ['Past performance is not a reliable indicator of future results.'],
  source_map: { 'attr:alloc': 'Allocation +35 bps' },
  compliance_status: 'passed',
  inserted_disclaimers: [],
  rejections: [],
}

describe('CommentaryViewer', () => {
  it('renders a clickable source chip for each claim value', () => {
    render(<CommentaryViewer commentary={commentary} />)
    expect(screen.getByRole('button', { name: '+35 bps' })).toBeInTheDocument()
  })

  it('renders inserted disclosures', () => {
    render(<CommentaryViewer commentary={commentary} />)
    expect(screen.getByText(/not a reliable indicator/i)).toBeInTheDocument()
  })
})
