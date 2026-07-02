import type { Audience } from '@/types/commentary'

interface AudienceSelectorProps {
  value: Audience
  onChange: (audience: Audience) => void
}

const OPTIONS: { value: Audience; label: string }[] = [
  { value: 'client', label: 'Client' },
  { value: 'institutional', label: 'Institutional' },
  { value: 'ic', label: 'Investment Committee' },
]

export default function AudienceSelector({ value, onChange }: AudienceSelectorProps) {
  return (
    <div className="inline-flex rounded-lg border border-border bg-surface-50 p-0.5">
      {OPTIONS.map((opt) => (
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
  )
}
