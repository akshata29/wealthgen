import { useState } from 'react'

interface SourcePopoverProps {
  sourceId: string
  citation: string | undefined
  value?: string | null
  confidence?: number | null
}

/** A clickable source chip that reveals the citation for a numeric claim. */
export default function SourcePopover({
  sourceId,
  citation,
  value,
  confidence,
}: SourcePopoverProps) {
  const [open, setOpen] = useState(false)
  const resolved = Boolean(citation)
  const lowConfidence = confidence != null && confidence < 0.7

  return (
    <span className="relative inline-block">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={
          resolved && !lowConfidence
            ? 'badge-info cursor-pointer'
            : 'badge-warning cursor-pointer'
        }
        title="Click to view source"
      >
        {value ?? sourceId}
      </button>
      {open && (
        <span className="absolute z-10 mt-1 left-0 w-72 card text-xs text-gray-300 shadow-lg">
          <span className="block section-title">Source</span>
          <span className="block font-mono text-[11px] text-gray-500 mb-1">{sourceId}</span>
          <span className="block text-gray-200">
            {citation ?? 'Unresolved source — blocked from delivery.'}
          </span>
          {confidence != null && (
            <span className="block mt-1 text-gray-500">
              Confidence: {(confidence * 100).toFixed(0)}%
              {lowConfidence && <span className="text-yellow-400"> · needs review</span>}
            </span>
          )}
        </span>
      )}
    </span>
  )
}
