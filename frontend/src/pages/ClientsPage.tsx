import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Radio } from 'lucide-react'
import PageHeader from '@/components/ui/PageHeader'
import ClientCard from '@/components/clients/ClientCard'
import EventBanner from '@/components/EventBanner'
import LiveEventBanner from '@/components/LiveEventBanner'
import * as api from '@/utils/apiClient'
import { isActionable } from '@/utils/commentaryStatus'
import type { ClientSummary, VixEvent } from '@/types/portfolio'
import type { CommentarySummary, LiveEvent } from '@/types/commentary'

interface Counts {
  total: number
  pending: number
}

export default function ClientsPage() {
  const navigate = useNavigate()
  const [clients, setClients] = useState<ClientSummary[]>([])
  const [events, setEvents] = useState<VixEvent[]>([])
  const [countsByClient, setCountsByClient] = useState<Record<string, Counts>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [segment, setSegment] = useState<string>('all')
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>([])
  const [scanning, setScanning] = useState(false)
  const [scanned, setScanned] = useState(false)
  const [latestPeriod, setLatestPeriod] = useState<string>('')

  async function scanLiveEvents() {
    setScanning(true)
    try {
      const [live, periods] = await Promise.all([api.getLiveEvents(3), api.getPeriods()])
      setLiveEvents(live)
      setLatestPeriod(periods.latest)
      setScanned(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Live event scan failed')
    } finally {
      setScanning(false)
    }
  }

  useEffect(() => {
    let active = true
    async function load() {
      try {
        const [c, e] = await Promise.all([api.getClients(), api.getVixEvents(true)])
        if (!active) return
        setClients(c)
        setEvents(e)
        // Commentary counts are best-effort (needs Cosmos); don't block the page.
        try {
          const all = await api.listAllCommentary()
          if (!active) return
          const mandateToClient = new Map<string, string>()
          c.forEach((cl) => cl.mandates.forEach((m) => mandateToClient.set(m.mandate_id, cl.client_id)))
          const counts: Record<string, Counts> = {}
          all.forEach((cm: CommentarySummary) => {
            const clientId = mandateToClient.get(cm.mandate_id)
            if (!clientId) return
            const entry = (counts[clientId] ??= { total: 0, pending: 0 })
            entry.total += 1
            if (isActionable(cm)) entry.pending += 1
          })
          setCountsByClient(counts)
        } catch {
          /* commentary store may be unavailable; leave counts empty */
        }
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : 'Failed to load clients')
      } finally {
        if (active) setLoading(false)
      }
    }
    load()
    return () => {
      active = false
    }
  }, [])

  const totalAum = clients.reduce((sum, c) => sum + c.total_aum_musd, 0)

  // Distinct client segments (e.g. Private Client, Family Office, Institutional).
  const segments = Array.from(new Set(clients.map((c) => c.segment))).sort()
  const filtered = segment === 'all' ? clients : clients.filter((c) => c.segment === segment)

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <PageHeader
        title="Clients & Portfolios"
        subtitle={
          loading
            ? 'Loading…'
            : `${clients.length} clients · $${totalAum.toFixed(0)}m total AUM`
        }
      />

      {error && <div className="badge-error">{error}</div>}

      {/* Live market-event scan (Web IQ) */}
      <div className="flex items-center gap-3 flex-wrap">
        <button className="btn-secondary" disabled={scanning} onClick={scanLiveEvents}>
          <span className="inline-flex items-center gap-2">
            <Radio size={14} />
            {scanning ? 'Scanning…' : 'Scan live market events (Web IQ)'}
          </span>
        </button>
        {scanned && liveEvents.length === 0 && (
          <span className="text-xs text-gray-500">
            No live events returned — Web IQ may be rate-limited; the scenario event below still works.
          </span>
        )}
      </div>

      {liveEvents.map((ev) => (
        <LiveEventBanner
          key={ev.event.source_id}
          item={ev}
          onGenerateBrief={(mandateId) =>
            navigate(
              `/generate?commentary_type=event_driven${
                mandateId ? `&mandate_id=${encodeURIComponent(mandateId)}` : ''
              }${latestPeriod ? `&period=${encodeURIComponent(latestPeriod)}` : ''}`,
            )
          }
        />
      ))}

      {events.length > 0 && (
        <div className="text-[11px] text-gray-500 -mb-2">Scenario event (demo dataset):</div>
      )}
      {events.map((e) => (
        <EventBanner key={e.period} event={e} />
      ))}

      {!loading && segments.length > 1 && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="section-title !mb-0">Filter by type</span>
          <div className="inline-flex rounded-lg border border-border bg-surface-50 p-0.5">
            {['all', ...segments].map((seg) => (
              <button
                key={seg}
                type="button"
                onClick={() => setSegment(seg)}
                className={
                  segment === seg
                    ? 'px-3 py-1.5 rounded-md text-sm font-medium bg-accent text-white'
                    : 'px-3 py-1.5 rounded-md text-sm font-medium text-gray-400 hover:text-gray-100'
                }
              >
                {seg === 'all' ? `All (${clients.length})` : seg}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map((c) => (
          <ClientCard
            key={c.client_id}
            client={c}
            commentaryCount={countsByClient[c.client_id]?.total ?? 0}
            pendingCount={countsByClient[c.client_id]?.pending ?? 0}
          />
        ))}
      </div>
    </div>
  )
}
