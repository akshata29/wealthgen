import type { CompliantCommentary } from '@/types/commentary'
import SourcePopover from './SourcePopover'

interface CommentaryViewerProps {
  commentary: CompliantCommentary
}

/** Renders the 7-section commentary; each claim value is a clickable source chip. */
export default function CommentaryViewer({ commentary }: CommentaryViewerProps) {
  return (
    <div className="space-y-5">
      {commentary.sections.map((section) => (
        <div key={section.heading} className="card">
          <div className="section-title">{section.heading}</div>
          <div className="space-y-2">
            {section.claims.map((claim, i) => (
              <p key={i} className="text-sm text-gray-200 leading-relaxed">
                {claim.text}{' '}
                <SourcePopover
                  sourceId={claim.source_id}
                  citation={commentary.source_map[claim.source_id]}
                  value={claim.value}
                  confidence={claim.confidence}
                />
              </p>
            ))}
          </div>
        </div>
      ))}

      {commentary.disclaimers.length > 0 && (
        <div className="card">
          <div className="section-title">Disclosures</div>
          <ul className="space-y-1 text-xs text-gray-500">
            {commentary.disclaimers.map((d, i) => (
              <li key={i}>• {d}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
