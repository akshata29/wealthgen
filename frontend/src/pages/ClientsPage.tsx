import { useEffect, useState } from 'react'
import PageHeader from '@/components/ui/PageHeader'
import ClientCard from '@/components/clients/ClientCard'
import EventBanner from '@/components/EventBanner'
import * as api from '@/utils/apiClient'
import { isActionable } from '@/utils/commentaryStatus'
import type { ClientSummary, VixEvent } from '@/types/portfolio'
import type { CommentarySummary } from '@/types/commentary'

interface Counts {
  total: number
  pending: number
}

export default function ClientsPage() {
  const [clients, setClients] = useState<ClientSummary[]>([])
  const [events, setEvents] = useState<VixEvent[]>([])
  const [countsByClient, setCountsByClient] = useState<Record<string, Counts>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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

      {events.map((e) => (
        <EventBanner key={e.period} event={e} />
      ))}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {clients.map((c) => (
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
