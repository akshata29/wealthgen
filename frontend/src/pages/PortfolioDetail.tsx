import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Sparkles } from 'lucide-react'
import PageHeader from '@/components/ui/PageHeader'
import StatGrid from '@/components/performance/StatGrid'
import BenchmarkCompare from '@/components/performance/BenchmarkCompare'
import SectorAttribution from '@/components/performance/SectorAttribution'
import IndexCompare from '@/components/performance/IndexCompare'
import NextBestActions from '@/components/NextBestActions'
import EventBanner from '@/components/EventBanner'
import MorningstarXray from '@/components/research/MorningstarXray'
import LsegMarketContext from '@/components/research/LsegMarketContext'
import CommentaryHistory from '@/components/CommentaryHistory'
import * as api from '@/utils/apiClient'
import type { NextBestAction, PerformanceReport, VixEvent } from '@/types/portfolio'

export default function PortfolioDetail() {
  const { mandateId = '' } = useParams()
  const navigate = useNavigate()

  const [periods, setPeriods] = useState<string[]>([])
  const [period, setPeriod] = useState<string>('')
  const [report, setReport] = useState<PerformanceReport | null>(null)
  const [actions, setActions] = useState<NextBestAction[]>([])
  const [event, setEvent] = useState<VixEvent | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // Load available periods once.
  useEffect(() => {
    api
      .getPeriods()
      .then((p) => {
        setPeriods(p.periods)
        setPeriod((cur) => cur || p.latest)
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load periods'))
  }, [])

  // Load the performance report + NBA + event whenever mandate/period changes.
  useEffect(() => {
    if (!mandateId || !period) return
    let active = true
    setLoading(true)
    Promise.all([
      api.getPerformance(mandateId, period),
      api.getNextBestActions(mandateId, period),
      api.getVixEvents(false),
    ])
      .then(([rep, nba, events]) => {
        if (!active) return
        setReport(rep)
        setActions(nba)
        setEvent(events.find((e) => e.period === period && e.event_trigger) ?? null)
        setError(null)
      })
      .catch((e) => active && setError(e instanceof Error ? e.message : 'Failed to load portfolio'))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [mandateId, period])

  function generateBrief(trigger: 'scheduled' | 'event') {
    const params = new URLSearchParams({ mandate_id: mandateId, period })
    if (trigger === 'event') params.set('trigger', 'event')
    navigate(`/generate?${params.toString()}`)
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <PageHeader
        title={report?.mandate.display_name ?? mandateId}
        subtitle={report ? `${report.mandate.strategy} · ${report.benchmark_name}` : 'Loading…'}
        actions={
          <div className="flex items-center gap-2">
            <select
              className="input !w-auto"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
            >
              {periods.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
            <button className="btn-primary" onClick={() => generateBrief('scheduled')}>
              <span className="inline-flex items-center gap-2">
                <Sparkles size={14} /> Generate commentary
              </span>
            </button>
          </div>
        }
      />

      {error && <div className="badge-error">{error}</div>}

      {event && <EventBanner event={event} onGenerateBrief={() => generateBrief('event')} />}

      {report && !loading && (
        <>
          <StatGrid summary={report.summary} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <BenchmarkCompare summary={report.summary} benchmarkName={report.benchmark_name} />
            <IndexCompare
              indexReturns={report.index_returns}
              portfolioReturn={report.summary.total_return_net_pct}
            />
          </div>

          <SectorAttribution
            contributors={report.top_contributors}
            detractors={report.top_detractors}
          />

          {report.positioning_changes.length > 0 && (
            <div className="card space-y-3">
              <h3 className="text-sm font-semibold text-gray-100">
                Positioning changes (what &amp; why)
              </h3>
              <div className="space-y-2">
                {report.positioning_changes.map((p) => (
                  <div
                    key={p.source_id}
                    className="rounded-lg border border-border bg-surface-50 p-3"
                  >
                    <div className="flex items-center gap-2">
                      <span className="badge-accent">{p.direction}</span>
                      <span className="text-sm text-gray-200">{p.description}</span>
                      {p.magnitude && (
                        <span className="text-xs text-gray-500 ml-auto">{p.magnitude}</span>
                      )}
                    </div>
                    {p.rationale && <p className="text-xs text-gray-400 mt-1.5">{p.rationale}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}

          <NextBestActions actions={actions} />

          <CommentaryHistory mandateId={mandateId} />

          <MorningstarXray mandateId={mandateId} period={period} />

          <LsegMarketContext mandateId={mandateId} period={period} />
        </>
      )}
    </div>
  )
}
