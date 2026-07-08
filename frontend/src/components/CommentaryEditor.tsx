import type { CommentarySection } from '@/types/commentary'

interface CommentaryEditorProps {
  sections: CommentarySection[]
  onChange: (sections: CommentarySection[]) => void
}

/** Editable draft — PM/advisor can revise each claim's text before re-running compliance. */
export default function CommentaryEditor({ sections, onChange }: CommentaryEditorProps) {
  function updateClaim(si: number, ci: number, text: string) {
    onChange(
      sections.map((s, i) =>
        i !== si
          ? s
          : { ...s, claims: s.claims.map((c, j) => (j !== ci ? c : { ...c, text })) },
      ),
    )
  }

  return (
    <div className="space-y-5">
      <div className="text-xs text-gray-400">
        Edit the wording below, then <span className="text-gray-200">Save changes</span> and{' '}
        <span className="text-gray-200">Re-run compliance</span>. Numbers and their sources stay
        linked — edit the narrative, not the figures.
      </div>
      {sections.map((section, si) => (
        <div key={section.heading} className="card">
          <div className="section-title">{section.heading}</div>
          <div className="space-y-3">
            {section.claims.map((claim, ci) => (
              <div key={ci} className="space-y-1">
                <textarea
                  className="input min-h-[3rem] resize-y"
                  value={claim.text}
                  onChange={(e) => updateClaim(si, ci, e.target.value)}
                />
                {(claim.value || claim.source_id) && (
                  <div className="text-[11px] text-gray-500">
                    {claim.value && <span className="text-gray-400">{claim.value}</span>}
                    {claim.value && claim.source_id && ' · '}
                    {claim.source_id && <span>source: {claim.source_id}</span>}
                  </div>
                )}
              </div>
            ))}
            {section.claims.length === 0 && (
              <p className="text-xs text-gray-500">No claims in this section.</p>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
