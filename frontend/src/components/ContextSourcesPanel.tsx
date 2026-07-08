import {
  Globe,
  Mail,
  Newspaper,
  Radio,
  Users,
  FileText,
  UserCog,
  LineChart,
  ExternalLink,
} from 'lucide-react'
import type { ContextChannel, ContextSource } from '@/types/commentary'

interface ContextSourcesPanelProps {
  sources: ContextSource[]
}

const CHANNEL_META: Record<
  ContextChannel,
  { label: string; icon: typeof Globe }
> = {
  advisor_portal: { label: 'Advisor portal', icon: Globe },
  fund_webpage: { label: 'Fund webpage', icon: FileText },
  market_commentary: { label: 'Market commentary', icon: Newspaper },
  portfolio_manager: { label: 'PM commentary', icon: UserCog },
  research: { label: 'Independent research (MCP)', icon: LineChart },
  webcast: { label: 'Webcast', icon: Radio },
  email_alert: { label: 'Email alert', icon: Mail },
  wholesaler: { label: 'Wholesaler note', icon: Users },
}

/** Shows the real-world market-context artefacts the brief drew on. */
export default function ContextSourcesPanel({ sources }: ContextSourcesPanelProps) {
  return (
    <div className="card space-y-3">
      <div>
        <h3 className="text-sm font-semibold text-gray-100">Real-world context used</h3>
        <p className="text-xs text-gray-400">
          Ad-hoc market updates an advisor reads — portals, fund pages, commentary, webcasts,
          alerts, and wholesaler notes. Cited in the narrative by source id.
        </p>
      </div>
      <ul className="space-y-2">
        {sources.map((src) => {
          const meta = CHANNEL_META[src.channel]
          const Icon = meta?.icon ?? Newspaper
          return (
            <li
              key={src.source_id}
              className="rounded-lg border border-border bg-surface-50 p-3"
            >
              <div className="flex items-center gap-2 flex-wrap">
                <span className="badge inline-flex items-center gap-1 text-xs">
                  <Icon size={12} /> {meta?.label ?? src.channel}
                </span>
                <span className="text-xs font-medium text-gray-200">{src.publisher}</span>
                {src.published && (
                  <span className="text-[11px] text-gray-500">{src.published}</span>
                )}
                {src.live && (
                  <span className="badge-success text-[11px]">live</span>
                )}
              </div>
              <div className="mt-1 text-sm text-gray-100">{src.title}</div>
              <p className="mt-1 text-xs text-gray-400">{src.summary}</p>
              {src.key_points && src.key_points.length > 0 && (
                <ul className="mt-2 space-y-0.5">
                  {src.key_points.map((kp, i) => (
                    <li key={i} className="text-xs text-gray-300">
                      • {kp}
                    </li>
                  ))}
                </ul>
              )}
              {src.affected_holdings && src.affected_holdings.length > 0 ? (
                <div className="mt-2 flex items-center gap-1 flex-wrap">
                  <span className="text-[11px] text-gray-500">Your holdings affected:</span>
                  {src.affected_holdings.map((h) => (
                    <span key={h.ticker} className="badge-warning text-[11px]">
                      {h.ticker} {(h.weight * 100).toFixed(1)}%
                    </span>
                  ))}
                </div>
              ) : (
                src.affected_tickers &&
                src.affected_tickers.length > 0 && (
                  <div className="mt-2 flex items-center gap-1 flex-wrap">
                    <span className="text-[11px] text-gray-500">Holdings affected:</span>
                    {src.affected_tickers.map((t) => (
                      <span key={t} className="badge-accent text-[11px]">
                        {t}
                      </span>
                    ))}
                  </div>
                )
              )}
              {src.advisor_talking_point && (
                <blockquote className="mt-2 border-l-2 border-accent pl-2 text-xs italic text-gray-300">
                  Advisor talking point: {src.advisor_talking_point}
                </blockquote>
              )}
              {src.url && (
                <a
                  href={src.url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-1 inline-flex items-center gap-1 text-xs text-accent hover:underline"
                >
                  <ExternalLink size={12} /> Open source
                </a>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
