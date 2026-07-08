import {
  Clock,
  Users,
  Presentation,
  PlayCircle,
  Network,
  TrendingUp,
  MessageCircleQuestion,
  ShieldCheck,
  Sparkles,
  AlertTriangle,
} from 'lucide-react'
import PageHeader from '@/components/ui/PageHeader'

/** ---- Run of show ------------------------------------------------------ */
interface Segment {
  n: number
  title: string
  time: string
  speaker: string
  onScreen: string
}

const RUN_OF_SHOW: Segment[] = [
  { n: 1, title: 'Cold open', time: '1 min', speaker: 'Joe', onScreen: 'Slide 1' },
  { n: 2, title: 'The problem in four numbers', time: '2.5 min', speaker: 'Joe', onScreen: 'Slide 2' },
  { n: 3, title: 'The workflow, grounded', time: '1.5 min', speaker: 'Joe', onScreen: 'Slide 3' },
  { n: 4, title: 'Live demo', time: '10 min', speaker: 'Ashish', onScreen: 'Slide 4 → live app' },
  { n: 5, title: 'Architecture + scale to production', time: '4 min', speaker: 'Karl', onScreen: 'Slide 5' },
  { n: 6, title: 'Business value → the ask', time: '1.5–2 min', speaker: 'Joe', onScreen: 'Slides 6 → 7' },
]

/** ---- Business talking points ------------------------------------------ */
const PROBLEM_NUMBERS = [
  { metric: '2 hrs', label: 'One bespoke narrative today', detail: 'Pull analytics, interpret for this client’s holdings, write at their literacy level, stay inside the regulatory lines.' },
  { metric: '20%', label: 'Coverage', detail: 'Only the top of the book gets bespoke commentary. Everyone else gets generic — or nothing. The math doesn’t work.' },
  { metric: '1,000', label: 'Advisors = 1,000 voices', detail: 'Compliance reviews by sampling. The variance itself is the risk.' },
  { metric: '40–60%', label: 'Non-client-facing work', detail: 'Commentary is one of the biggest chunks — and the chunk we can give back.' },
]

const WORKFLOW_STEPS = ['Ingest', 'Analyze', 'Contextualize', 'Draft', 'Guardrail']

const IMPACT = [
  { metric: '80%', label: 'Effort reduction', detail: 'Where commentary exists today — ~2 hrs down to ~10 min review.' },
  { metric: '5×', label: 'Coverage', detail: 'From a fifth of the book to all of it.' },
  { metric: 'Same day', label: 'Turnaround', detail: 'Hours to seconds — grounded, reviewed, delivered.' },
  { metric: '100%', label: 'Reviewed', detail: 'Compliance stops sampling and starts guaranteeing.' },
]

/** ---- Demo scenarios --------------------------------------------------- */
interface DemoStep {
  text: string
  money?: boolean
}

const SCENARIO_A: DemoStep[] = [
  { text: 'Setup: “It’s that Monday morning. Watch what happens for one of your advisor’s clients.”' },
  { text: 'Market event → briefing. Pass tickers/identifiers; holdings resolve; the workflow assembles the analysis.' },
  { text: 'Morningstar x-ray, live — sector, allocation, weights, risk/return, attribution on screen. “Independent analysis, every figure traceable.”' },
  { text: 'LSEG market context — the why behind the numbers.' },
  { text: 'Tone/literacy toggle — flip live. “This client is a retired teacher, not a CFA. Watch the same analysis become her language.”', money: true },
  { text: 'Reviewer approval → delivery. Approve, export PDF/Word, or send by email. “Reviewed by a human before it leaves the building.”' },
  { text: 'Closer: “A hundred clients. Same morning. Every one gets this.”' },
]

const SCENARIO_B: DemoStep[] = [
  { text: 'Setup: “Now the calmer, more common case — review season.”' },
  { text: 'On-demand briefing for tomorrow’s client meeting.' },
  { text: 'Life event → next-best-action. “Her daughter starts university next year.” The workflow surfaces a recommendation alongside the commentary.', money: true },
  { text: 'Same firm voice, different client. “A thousand advisors. One voice.”' },
  { text: 'Closer: “Hours to seconds — grounded, reviewed, delivered.”' },
]

/** ---- Architecture layers (story mapping) ------------------------------ */
const ARCH_LAYERS = [
  {
    layer: 'Provider intelligence',
    highlight: false,
    detail: 'Morningstar & LSEG over a direct MCP client; one-time OAuth with a stored refresh token, backend mints access tokens headlessly; attribution preserved on every figure. (The hallucination answer lives here.)',
  },
  {
    layer: 'Enterprise data',
    highlight: false,
    detail: 'Fabric / OneLake holds holdings, client portfolios, weights, attribution; a Fabric Data Agent sits on top, with a Fabric ontology for business-entity relationships.',
  },
  {
    layer: 'Knowledge & guardrails',
    highlight: true,
    detail: 'Work IQ carries approved language, the disclosure library, tone playbooks, and next-best-action rules. Foundry IQ grounds fund/ETF facts and benchmark data (e.g., MSCI ACWI). “This layer is why it’s a compliance product, not a chatbot.”',
  },
  {
    layer: 'Orchestration',
    highlight: false,
    detail: 'The Foundry agent coordinates the tools; human approval gates delivery; PDF, Word, or email out the other side.',
  },
]

const ROLLOUT = [
  'Built on FSI accelerators.',
  'Much of the prototype built by a Copilot multi-agent workflow — 3 custom agents (research-plan-implement), packaged as a Financial Services Copilot extension. Working software in ~2 weeks, essentially no hand-written code.',
  'Shared subscription migration underway — resources scripted so the whole team runs one environment.',
  'Enterprise security posture: private link, VNet, firewall.',
]

/** ---- Q&A -------------------------------------------------------------- */
const QA = [
  { q: 'How do you avoid hallucination?', a: 'Grounded by design: provider figures from live Morningstar/LSEG MCP calls with per-figure attribution; approved language from Work IQ; human approval before delivery.' },
  { q: 'What’s synthetic vs. real?', a: 'Morningstar integration is live; some client data is synthetic while the shared environment completes; identical architecture either way.' },
  { q: 'How does this scale into our environment?', a: 'Modular by function; shared-subscription migration underway with scripted provisioning; private link, VNet, firewall posture.' },
  { q: 'Where do compliance controls live?', a: 'Work IQ (approved language, disclosures, playbooks) plus a mandatory human approval gate; attribution and audit per narrative.' },
  { q: 'Where do the impact numbers come from?', a: 'Stated-assumption model — the structure (efficiency + coverage + risk) holds at any parameters; we’d calibrate in the POC.' },
  { q: 'Won’t advisors distrust AI-written comms?', a: 'The advisor stays the author of record; grounding + review shrink the burden rather than shift it.' },
  { q: 'Fabric vs. Foundry IQ vs. Work IQ?', a: 'Fabric: structured client/portfolio data + data agent + ontology. Foundry IQ: unstructured fund/benchmark facts. Work IQ: communication guidance — style, approved language, playbooks, NBA rules. MCP: live provider intelligence.' },
  { q: 'How fast could a POC start?', a: 'The shared environment is being stood up now and provisioning is scripted — a POC scopes to one advisor workflow and the firm’s templates.' },
]

const CONTINGENCY = [
  'Recorded backup exists (shareable after). Narrate over it with the same beats if live fails.',
  'Pre-export a PDF and keep it in a tab — never demo the export retry.',
  'Real vs. synthetic: “The Morningstar integration is live. Some client data is synthetic while we finish the shared environment — the architecture is identical either way.”',
  'Discipline: Q&A answers under 45 seconds. Rabbit holes get “happy to go deep after — short version is…”.',
]

function Money() {
  return <span className="badge-gold text-[10px] ml-2">money moment</span>
}

export default function DemoFlowPage() {
  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <PageHeader
        title="Demo Flow — July 9 Readout"
        subtitle="Run of show + narration for the 30-minute mock customer meeting (AWM Pod 1 · Portfolio Narrative Generator)"
      />

      {/* Meta strip */}
      <div className="flex flex-wrap gap-2 text-xs">
        <span className="badge inline-flex items-center gap-1"><Clock size={12} /> 12:00–12:30 PM ET · 30 min</span>
        <span className="badge inline-flex items-center gap-1"><Presentation size={12} /> ~20 min present · ~10 min Q&amp;A</span>
        <span className="badge inline-flex items-center gap-1"><Users size={12} /> Joe (business) · Ashish (demo) · Karl (architecture)</span>
        <span className="badge-info">Principle: slides carry the numbers, the speaker carries the story — never read a slide.</span>
      </div>

      {/* Run of show */}
      <div className="card space-y-3">
        <h3 className="text-sm font-semibold text-gray-100">Run of show</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-500 border-b border-border">
                <th className="py-2 pr-3 font-medium">#</th>
                <th className="py-2 px-3 font-medium">Segment</th>
                <th className="py-2 px-3 font-medium">Time</th>
                <th className="py-2 px-3 font-medium">Speaker</th>
                <th className="py-2 pl-3 font-medium">On screen</th>
              </tr>
            </thead>
            <tbody>
              {RUN_OF_SHOW.map((s) => (
                <tr key={s.n} className="border-b border-border/50 last:border-0">
                  <td className="py-2 pr-3 text-gray-500">{s.n}</td>
                  <td className="py-2 px-3 text-gray-100">{s.title}</td>
                  <td className="py-2 px-3 text-gray-400 tabular-nums">{s.time}</td>
                  <td className="py-2 px-3 text-gray-300">{s.speaker}</td>
                  <td className="py-2 pl-3 text-gray-400">{s.onScreen}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-[11px] text-gray-500">
          Buffer lives inside the demo. If it runs long, the business-value close compresses to two
          sentences; if the whole session runs long, Q&amp;A absorbs it.
        </p>
      </div>

      {/* Segment 1 — cold open */}
      <div className="card space-y-2">
        <div className="flex items-center gap-2">
          <span className="badge-accent">1 · Joe · 1 min</span>
          <h3 className="text-sm font-semibold text-gray-100">Cold open</h3>
        </div>
        <blockquote className="border-l-2 border-accent pl-3 text-sm text-gray-300 italic">
          “It’s 9:47 on a Monday morning. The market opened down three and a half percent. An
          advisor’s phone is already ringing — and it’s going to ring a hundred more times today,
          because every client has the same question: what just happened to my money? A real answer
          — about their portfolio, not the market in general — takes about two hours. She has a
          hundred clients. And one day. That’s the problem we picked.”
        </blockquote>
      </div>

      {/* Segment 2 — four numbers */}
      <div className="card space-y-3">
        <div className="flex items-center gap-2">
          <span className="badge-accent">2 · Joe · 2.5 min</span>
          <h3 className="text-sm font-semibold text-gray-100">The problem in four numbers</h3>
          <span className="text-[11px] text-gray-500">one beat per number, pause between</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {PROBLEM_NUMBERS.map((p) => (
            <div key={p.metric} className="rounded-lg border border-border bg-surface-50 p-3">
              <div className="text-2xl font-bold text-accent">{p.metric}</div>
              <div className="text-xs font-medium text-gray-200 mt-1">{p.label}</div>
              <div className="text-[11px] text-gray-400 mt-1">{p.detail}</div>
            </div>
          ))}
        </div>
        <p className="text-sm text-gray-300">
          Transition: <span className="italic">“What if a bespoke, compliant, grounded narrative cost seconds instead of hours?”</span>
        </p>
      </div>

      {/* Segment 3 — workflow */}
      <div className="card space-y-3">
        <div className="flex items-center gap-2">
          <span className="badge-accent">3 · Joe · 1.5 min</span>
          <h3 className="text-sm font-semibold text-gray-100">The workflow, grounded</h3>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {WORKFLOW_STEPS.map((step, i) => (
            <div key={step} className="flex items-center gap-2">
              <span className="badge-info">{step}</span>
              {i < WORKFLOW_STEPS.length - 1 && <span className="text-gray-600">→</span>}
            </div>
          ))}
        </div>
        <ul className="text-xs text-gray-400 space-y-1 list-disc pl-4">
          <li>Grounded in trusted providers — not a chatbot on portfolio data.</li>
          <li>Portfolio analysis = a real Morningstar x-ray (sector, allocation, weights, risk/return) over MCP.</li>
          <li>Market context from LSEG; every figure keeps its provider attribution.</li>
          <li>Draft against your firm’s template — tone, literacy level, plain non-financial language.</li>
          <li>Guardrail: draft → review → approve → deliver. Human sign-off is built in, not optional.</li>
        </ul>
      </div>

      {/* Segment 4 — live demo */}
      <div className="card space-y-4">
        <div className="flex items-center gap-2">
          <span className="badge-accent inline-flex items-center gap-1"><PlayCircle size={12} /> 4 · Ashish · 10 min</span>
          <h3 className="text-sm font-semibold text-gray-100">Live demo</h3>
          <span className="text-[11px] text-gray-500">Slide 4 map for 15s, then the app</span>
        </div>

        <div>
          <div className="section-title !mb-2 flex items-center gap-2">
            Scenario A — The Market-Event Morning <span className="text-gray-500">~6 min</span>
          </div>
          <ul className="space-y-1.5">
            {SCENARIO_A.map((step, i) => (
              <li key={i} className="text-xs text-gray-300 flex items-start gap-2">
                <span className="text-gray-600 mt-0.5">{i + 1}.</span>
                <span>{step.text}{step.money && <Money />}</span>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <div className="section-title !mb-2 flex items-center gap-2">
            Scenario B — The Quarterly Review <span className="text-gray-500">~4 min</span>
          </div>
          <ul className="space-y-1.5">
            {SCENARIO_B.map((step, i) => (
              <li key={i} className="text-xs text-gray-300 flex items-start gap-2">
                <span className="text-gray-600 mt-0.5">{i + 1}.</span>
                <span>{step.text}{step.money && <Money />}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-lg border border-yellow-800/40 bg-yellow-900/10 p-3">
          <div className="flex items-center gap-2 text-yellow-400 text-xs font-medium">
            <AlertTriangle size={13} /> Contingency &amp; honesty lines (prep, not slides)
          </div>
          <ul className="mt-2 text-[11px] text-gray-300 space-y-1 list-disc pl-4">
            {CONTINGENCY.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* Segment 5 — architecture */}
      <div className="card space-y-3">
        <div className="flex items-center gap-2">
          <span className="badge-accent inline-flex items-center gap-1"><Network size={12} /> 5 · Karl · 4 min</span>
          <h3 className="text-sm font-semibold text-gray-100">Architecture + scale to production</h3>
        </div>
        <div className="space-y-2">
          {ARCH_LAYERS.map((l) => (
            <div
              key={l.layer}
              className={
                l.highlight
                  ? 'rounded-lg border border-accent/50 bg-accent/10 p-3'
                  : 'rounded-lg border border-border bg-surface-50 p-3'
              }
            >
              <div className="text-sm font-medium text-gray-100 flex items-center gap-2">
                {l.highlight && <ShieldCheck size={14} className="text-accent" />}
                {l.layer}
              </div>
              <div className="text-[11px] text-gray-400 mt-1">{l.detail}</div>
            </div>
          ))}
        </div>
        <div>
          <div className="section-title !mb-2 flex items-center gap-2"><Sparkles size={12} /> Rollout vision (briskly)</div>
          <ul className="text-[11px] text-gray-400 space-y-1 list-disc pl-4">
            {ROLLOUT.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
        <p className="text-sm text-gray-300 italic">
          Segment close: “…which sets up the natural next step: a focused proof of concept.”
        </p>
      </div>

      {/* Segment 6 — business value */}
      <div className="card space-y-3">
        <div className="flex items-center gap-2">
          <span className="badge-accent inline-flex items-center gap-1"><TrendingUp size={12} /> 6 · Joe · 1.5–2 min</span>
          <h3 className="text-sm font-semibold text-gray-100">Business value → the ask</h3>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {IMPACT.map((p) => (
            <div key={p.metric} className="rounded-lg border border-border bg-surface-50 p-3">
              <div className="text-2xl font-bold text-green-400">{p.metric}</div>
              <div className="text-xs font-medium text-gray-200 mt-1">{p.label}</div>
              <div className="text-[11px] text-gray-400 mt-1">{p.detail}</div>
            </div>
          ))}
        </div>
        <blockquote className="border-l-2 border-accent pl-3 text-sm text-gray-300 italic">
          “Advisors don’t need help caring about their clients. They need the hours back to show it.
          Here’s where we’d go next: a focused POC — one real advisor workflow, your templates, your
          compliance rules, your data, in a shared environment. Validate it where it matters, then
          scale it on the architecture you just saw. We’d love your questions.”
        </blockquote>
        <p className="text-[11px] text-gray-500">
          Compressed if running long: ~20,000 advisor-hours a quarter returned to client
          conversations; every narrative passes the same review gate.
        </p>
      </div>

      {/* Q&A */}
      <div className="card space-y-3">
        <div className="flex items-center gap-2">
          <MessageCircleQuestion size={15} className="text-gray-300" />
          <h3 className="text-sm font-semibold text-gray-100">Q&amp;A — ~10 min · answers under 45 seconds</h3>
        </div>
        <div className="space-y-2">
          {QA.map((item) => (
            <div key={item.q} className="rounded-lg border border-border bg-surface-50 p-3">
              <div className="text-sm text-gray-100 font-medium">{item.q}</div>
              <div className="text-[11px] text-gray-400 mt-1">{item.a}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
