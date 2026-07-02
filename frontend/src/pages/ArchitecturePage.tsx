import PageHeader from '@/components/ui/PageHeader'

interface ServiceCard {
  name: string
  role: string
  sdk: string
  status: 'GA' | 'Preview'
}

const SERVICES: ServiceCard[] = [
  { name: 'Foundry IQ', role: 'Grounding hub — knowledge base + agentic retrieval (MCP)', sdk: 'azure-ai-projects 2.3.0', status: 'GA' },
  { name: 'Foundry Agent Service', role: 'Responses-based agents (create_version)', sdk: 'azure-ai-projects 2.3.0', status: 'GA' },
  { name: 'Fabric IQ', role: 'Holdings, weights, Brinson attribution (Data Agent + Ontology)', sdk: 'azure-search-documents (preview)', status: 'Preview' },
  { name: 'Work IQ', role: 'House view, style guide, disclosure library (M365)', sdk: 'azure-search-documents (preview)', status: 'Preview' },
  { name: 'Web IQ', role: 'Live market/macro context', sdk: 'azure-search-documents (preview)', status: 'Preview' },
  { name: 'Azure AI Content Understanding', role: 'Primary PDF path — tables + chart values + fields', sdk: 'azure-ai-contentunderstanding 1.1.0', status: 'GA' },
  { name: 'Azure AI Search', role: 'PDF source index (hybrid + semantic)', sdk: 'azure-search-documents', status: 'GA' },
  { name: 'Azure Cosmos DB', role: 'Drafts, versions, approval state, audit', sdk: 'azure-cosmos 4.7', status: 'GA' },
  { name: 'Azure AI Content Safety', role: 'Input + output safety checks', sdk: 'azure-ai-contentsafety 1.0', status: 'GA' },
  { name: 'LSEG (MCP)', role: 'Index returns, FX, pricing', sdk: 'MCP connector', status: 'GA' },
]

export default function ArchitecturePage() {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <PageHeader
        title="Architecture"
        subtitle="Azure services grounding the Portfolio Narrative Generator"
      />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {SERVICES.map((s) => (
          <div key={s.name} className="card space-y-1">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold text-gray-100">{s.name}</div>
              <span className={s.status === 'GA' ? 'badge-success' : 'badge-warning'}>{s.status}</span>
            </div>
            <div className="text-xs text-gray-400">{s.role}</div>
            <div className="text-[11px] font-mono text-gray-500">{s.sdk}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
