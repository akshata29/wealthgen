import type { BriefTrigger, Literacy, NarrativeStyle, Tone } from '@/types/commentary'

interface ToneControlsProps {
  style: NarrativeStyle
  onStyleChange: (style: NarrativeStyle) => void
  trigger: BriefTrigger
  onTriggerChange: (trigger: BriefTrigger) => void
}

const TONES: { value: Tone; label: string }[] = [
  { value: 'warm', label: 'Warm' },
  { value: 'neutral', label: 'Neutral' },
  { value: 'formal', label: 'Formal' },
]

const LITERACIES: { value: Literacy; label: string }[] = [
  { value: 'novice', label: 'Novice' },
  { value: 'informed', label: 'Informed' },
  { value: 'expert', label: 'Expert' },
]

const TRIGGERS: { value: BriefTrigger; label: string }[] = [
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'ad_hoc', label: 'Ad-hoc' },
  { value: 'event', label: 'Event' },
]

function Segmented<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: T
  options: { value: T; label: string }[]
  onChange: (v: T) => void
}) {
  return (
    <div>
      <span className="section-title">{label}</span>
      <div className="inline-flex rounded-lg border border-border bg-surface-50 p-0.5">
        {options.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={
              value === opt.value
                ? 'px-3 py-1.5 rounded-md text-sm font-medium bg-accent text-white'
                : 'px-3 py-1.5 rounded-md text-sm font-medium text-gray-400 hover:text-gray-100'
            }
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  )
}

/** Tone / ease / trigger dials that shape the generated narrative. */
export default function ToneControls({
  style,
  onStyleChange,
  trigger,
  onTriggerChange,
}: ToneControlsProps) {
  return (
    <div className="card space-y-4">
      <h3 className="text-sm font-semibold text-gray-100">Tone &amp; delivery</h3>
      <div className="flex flex-wrap gap-6">
        <Segmented
          label="Tone"
          value={style.tone}
          options={TONES}
          onChange={(tone) => onStyleChange({ ...style, tone })}
        />
        <Segmented
          label="Ease (literacy)"
          value={style.literacy}
          options={LITERACIES}
          onChange={(literacy) => onStyleChange({ ...style, literacy })}
        />
        <Segmented label="Trigger" value={trigger} options={TRIGGERS} onChange={onTriggerChange} />
      </div>
      <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
        <input
          type="checkbox"
          className="accent-accent"
          checked={style.non_financial_language}
          onChange={(e) =>
            onStyleChange({ ...style, non_financial_language: e.target.checked })
          }
        />
        Non-financial language (plain-English mode)
      </label>
    </div>
  )
}
