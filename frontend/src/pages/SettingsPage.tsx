import { useEffect, useState } from 'react'
import PageHeader from '@/components/ui/PageHeader'
import * as api from '@/utils/apiClient'

export default function SettingsPage() {
  const [info, setInfo] = useState<api.SettingsInfo | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .getSettings()
      .then(setInfo)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load settings'))
  }, [])

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <PageHeader title="Settings" subtitle="Jurisdictions, audience defaults, and endpoint status" />
      {error && <div className="badge-error">{error}</div>}

      <div className="card">
        <div className="section-title">Compliance jurisdictions</div>
        <div className="flex gap-2">
          {(info?.jurisdictions ?? ['UK', 'US']).map((j) => (
            <span key={j} className="badge-accent">
              {j}
            </span>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="section-title">Default audience</div>
        <div className="text-sm text-gray-200">{info?.default_audience ?? 'client'}</div>
      </div>

      <div className="card">
        <div className="section-title">Azure endpoint status</div>
        <div className="grid grid-cols-2 gap-2">
          {info &&
            Object.entries(info.endpoints).map(([name, ok]) => (
              <div key={name} className="flex items-center justify-between text-sm">
                <span className="text-gray-400 capitalize">{name.replace('_', ' ')}</span>
                <span className={ok ? 'badge-success' : 'badge-error'}>
                  {ok ? 'configured' : 'missing'}
                </span>
              </div>
            ))}
        </div>
      </div>
    </div>
  )
}
