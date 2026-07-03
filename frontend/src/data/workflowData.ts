import type { WorkflowTab } from '@/types/workflowTypes'

// Portfolio Narrative Generator — end-to-end grounded commentary pipeline.
// Node colors by type: service=blue, agent=indigo, gate=amber, datastore=teal, outcome=green.
export const workflowTabs: WorkflowTab[] = [
  {
    id: 'portfolio-commentary',
    label: 'Portfolio Commentary',
    description:
      'Ingest fund PDFs and validated analytics, ground every claim through the Foundry IQ ' +
      'knowledge base (Fabric IQ, Work IQ, Web IQ) — or, in local grounding mode, the validated ' +
      'reference dataset — draft the seven-section commentary in the house voice, substantiate ' +
      'every number, enforce compliance, and gate delivery on PM + Compliance sign-off.',
    nodes: [
      {
        id: 'doc-intel',
        type: 'agent',
        label: 'DocumentIntelligenceAgent',
        subtitle: 'agent · document_intelligence_agent.py',
        position: { x: 40, y: 40 },
        detail: {
          title: 'DocumentIntelligenceAgent',
          subtitle: 'agent · document_intelligence_agent.py',
          description:
            'Parses fund fact sheets and manager commentary PDFs with Azure AI Content ' +
            'Understanding into typed, validated facts — attribution tables, chart values, and ' +
            'fund metrics — each with a confidence score and source region.',
          sourceFiles: [
            'backend/app/agents/document_intelligence_agent.py',
            'backend/app/services/content_understanding.py',
          ],
          responsibilities: [
            'Run the custom fact-sheet analyzer (Content Understanding)',
            'Map Table/Generate/Extract fields to SourceFacts',
            'Flag low-confidence chart values for human review',
            'Upsert facts to the PDF source index',
          ],
          dataFlow: [
            'PDF (SAS URL) → Content Understanding analyzer',
            'Fields + tables + confidence + source region',
            'SourceFact[] → PDF Source Index',
          ],
          technologies: ['Azure AI Content Understanding', 'Azure AI Search'],
          keyFacts: ['Chart values are read directly; low-confidence fields gated for review'],
        },
      },
      {
        id: 'portfolio',
        type: 'agent',
        label: 'PortfolioAnalysisAgent',
        subtitle: 'agent · portfolio_analysis_agent.py',
        position: { x: 40, y: 180 },
        detail: {
          title: 'PortfolioAnalysisAgent',
          subtitle: 'agent · portfolio_analysis_agent.py',
          description:
            'Narrates pre-computed Brinson-Fachler attribution from Fabric IQ. Identifies top ' +
            'contributors/detractors and material positioning changes. Never recomputes attribution.',
          sourceFiles: ['backend/app/agents/portfolio_analysis_agent.py'],
          responsibilities: [
            'Ground on Fabric IQ (holdings, weights, attribution)',
            'Rank top 3 contributors and detractors by total effect',
            'Diff positioning versus the prior period',
          ],
          dataFlow: [
            'Fabric IQ (via Foundry IQ KB) → agent',
            'AnalysisFindings JSON with per-figure source_id',
          ],
          technologies: ['Fabric IQ', 'Foundry IQ', 'azure-ai-projects 2.x'],
          keyFacts: [
            'Consumes attribution; never recomputes it',
            'GROUNDING_MODE=local: reads the reference dataset (Microsoft Fabric) directly + surfaces top holdings',
          ],
        },
      },
      {
        id: 'market',
        type: 'agent',
        label: 'MarketIntelligenceAgent',
        subtitle: 'agent · market_intelligence_agent.py',
        position: { x: 300, y: 180 },
        detail: {
          title: 'MarketIntelligenceAgent',
          subtitle: 'agent · market_intelligence_agent.py',
          description:
            'Assembles the Market Context section from Web IQ themes and LSEG index/FX data. ' +
            'Uses no client data.',
          sourceFiles: ['backend/app/agents/market_intelligence_agent.py'],
          responsibilities: [
            'Fetch index returns and FX moves from LSEG (MCP)',
            'Ground market themes via Web IQ',
            'Return MarketContextFacts with per-fact source_id',
          ],
          dataFlow: ['Web IQ + LSEG MCP → agent', 'MarketContextFacts'],
          technologies: ['Web IQ', 'LSEG MCP', 'Foundry IQ'],
          keyFacts: [
            'GROUNDING_MODE=local: index/FX/themes come from the reference dataset (Microsoft Fabric)',
          ],
        },
      },
      {
        id: 'foundry-iq',
        type: 'service',
        label: 'Foundry IQ Knowledge Base',
        subtitle: 'service · foundry_iq.py',
        position: { x: 560, y: 110 },
        detail: {
          title: 'Foundry IQ Knowledge Base',
          subtitle: 'service · foundry_iq.py',
          description:
            'The grounding hub. A single knowledge base runs agentic retrieval across the PDF ' +
            'index, Fabric IQ, Work IQ, and Web IQ, returning one citation-backed answer via the ' +
            'MCP tool knowledge_base_retrieve.',
          sourceFiles: ['backend/app/services/foundry_iq.py'],
          responsibilities: [
            'Expose the KB as an MCP tool to Foundry agents',
            'Aggregate PDF index + Fabric IQ + Work IQ + Web IQ',
            'Return citation-backed retrieval results',
          ],
          dataFlow: [
            'Agent query → knowledge_base_retrieve (MCP)',
            'Cross-source agentic retrieval → cited passages',
          ],
          technologies: ['Foundry IQ', 'Azure AI Search', 'MCP', 'azure-ai-projects 2.x'],
        },
      },
      {
        id: 'refdata',
        type: 'datastore',
        label: 'Reference Dataset',
        subtitle: 'datastore · reference_data.py',
        position: { x: 560, y: 250 },
        detail: {
          title: 'Reference Dataset (Microsoft Fabric / OneLake)',
          subtitle: 'datastore · reference_data.py',
          description:
            'Clients, mandates, holdings, Brinson-Fachler attribution, performance, and market ' +
            'context served from a Microsoft Fabric Warehouse (Delta tables over OneLake) via the ' +
            'SQL analytics endpoint. In GROUNDING_MODE=local this is the validated source the ' +
            'analysis and market agents read directly; DATA_SOURCE_MODE=csv keeps a local-dev fallback.',
          sourceFiles: [
            'backend/app/services/reference_data.py',
            'backend/app/services/fabric_data.py',
            'backend/scripts/synthetic/generate.py',
          ],
          responsibilities: [
            'Serve clients / mandates / holdings / attribution / performance',
            'Provide market index + FX + VIX event context',
            'Back the Clients & Portfolios workspace and performance widgets',
          ],
          dataFlow: [
            'Fabric Warehouse (OneLake) → SQL endpoint → typed models',
            'AnalysisFindings + MarketContextFacts (local mode)',
          ],
          technologies: [
            'Microsoft Fabric Warehouse',
            'OneLake',
            'Fabric SQL endpoint',
            'Reconciled Brinson-Fachler',
            'Deterministic seed',
          ],
          keyFacts: ['Attribution reconciles to active return within 1bp'],
        },
      },
      {
        id: 'pdf-index',
        type: 'datastore',
        label: 'PDF Source Index',
        subtitle: 'datastore · search_index.py',
        position: { x: 300, y: 40 },
        detail: {
          title: 'PDF Source Index',
          subtitle: 'datastore · search_index.py',
          description:
            'Azure AI Search index of the SourceFacts extracted from PDFs (vector + semantic). ' +
            'A knowledge source for the Foundry IQ knowledge base.',
          sourceFiles: ['backend/app/services/search_index.py'],
          responsibilities: [
            'Store extracted facts as searchable, vectorized docs',
            'Serve hybrid + semantic retrieval',
          ],
          dataFlow: ['SourceFact[] → index docs', 'Hybrid query → grounded passages'],
          technologies: ['Azure AI Search', 'Integrated vectorization'],
        },
      },
      {
        id: 'narrative',
        type: 'agent',
        label: 'NarrativeGeneratorAgent',
        subtitle: 'agent · narrative_generator_agent.py',
        position: { x: 300, y: 320 },
        detail: {
          title: 'NarrativeGeneratorAgent',
          subtitle: 'agent · narrative_generator_agent.py',
          description:
            'Drafts the seven-section commentary in the house voice (grounded on Work IQ). Emits ' +
            'a typed CommentaryDraft where every numeric claim carries a source_id.',
          sourceFiles: ['backend/app/agents/narrative_generator_agent.py'],
          responsibilities: [
            'Ground house voice via Work IQ',
            'Emit JSON-only CommentaryDraft (7 sections)',
            'Attach a source_id to every numeric claim',
          ],
          dataFlow: [
            'Analysis + Market + SourceFacts + house voice → agent',
            'CommentaryDraft JSON',
          ],
          technologies: ['Work IQ', 'Foundry IQ', 'azure-ai-projects 2.x'],
          keyFacts: [
            'Temperature ≤ 0.2; JSON contract enforced',
            'Tone / ease / trigger dials; in local mode runs with no KB tool',
          ],
        },
      },
      {
        id: 'substantiation',
        type: 'gate',
        label: 'Substantiation Gate',
        subtitle: 'gate · substantiation.py',
        position: { x: 560, y: 390 },
        detail: {
          title: 'Substantiation Gate',
          subtitle: 'gate · substantiation.py',
          description:
            'The "no fabricated numbers" enforcement. Every SourcedClaim must reference a ' +
            'source_id present in the draft\'s source map; any unresolved claim blocks the draft ' +
            '(HTTP 422). A repair pass remaps or drops uncited claims before this check.',
          sourceFiles: [
            'backend/app/services/substantiation.py',
            'backend/app/agents/narrative_generator_agent.py',
          ],
          responsibilities: [
            'Verify every claim source_id resolves in the source map',
            'Reject drafts with unresolved (fabricated) figures',
            'Keep numbers tied to Fabric IQ / LSEG / Work IQ sources',
          ],
          dataFlow: ['CommentaryDraft → substantiate()', 'unresolved[] → 422 | pass'],
          technologies: ['Pydantic', 'FastAPI'],
          keyFacts: ['A number with no source never reaches compliance'],
        },
      },
      {
        id: 'compliance',
        type: 'agent',
        label: 'ComplianceGuardAgent',
        subtitle: 'agent · compliance_guard_agent.py',
        position: { x: 300, y: 460 },
        detail: {
          title: 'ComplianceGuardAgent',
          subtitle: 'agent · compliance_guard_agent.py',
          description:
            'Deterministic gate for UK (FCA) + US (SEC/FINRA): blocks forbidden language, checks ' +
            'fair-and-balanced and gross/net pairing, and inserts approved disclaimers.',
          sourceFiles: [
            'backend/app/agents/compliance_guard_agent.py',
            'backend/app/services/compliance/rules.py',
            'backend/app/services/compliance/disclosures.py',
          ],
          responsibilities: [
            'Reject guarantees/predictions/promissory language',
            'Enforce fair-and-balanced + gross/net pairing',
            'Insert jurisdiction-routed approved disclaimers',
          ],
          dataFlow: ['CommentaryDraft → rule engine', 'CompliantCommentary | RejectionReasons'],
          technologies: ['FCA COBS', 'SEC Marketing Rule', 'FINRA 2210'],
        },
      },
      {
        id: 'store',
        type: 'datastore',
        label: 'Commentary Store',
        subtitle: 'datastore · commentary_store.py',
        position: { x: 300, y: 600 },
        detail: {
          title: 'Commentary Store',
          subtitle: 'datastore · commentary_store.py',
          description:
            'Cosmos DB store for drafts, versions, source-map, approval state, and the immutable ' +
            'audit trail. Partition key /mandate_id.',
          sourceFiles: [
            'backend/app/services/commentary_store.py',
            'backend/app/services/audit.py',
          ],
          responsibilities: [
            'Persist drafts and versions',
            'Track PM + Compliance approval state',
            'Write immutable, PII-masked audit records',
          ],
          dataFlow: ['CompliantCommentary → Cosmos', 'Approval + audit updates'],
          technologies: ['Azure Cosmos DB'],
        },
      },
      {
        id: 'gate',
        type: 'gate',
        label: 'PM + Compliance Review Gate',
        subtitle: 'gate · ReviewApproval.tsx',
        position: { x: 210, y: 720 },
        detail: {
          title: 'PM + Compliance Review Gate',
          subtitle: 'gate · human-in-the-loop',
          description:
            'The PM edits and approves, then Compliance signs off. Delivery is blocked until both ' +
            'approvals are recorded. Every action is audit-logged.',
          sourceFiles: [
            'frontend/src/pages/ReviewApproval.tsx',
            'backend/app/routers/approvals.py',
          ],
          responsibilities: [
            'PM review + edit in-flow',
            'PM approval, then Compliance sign-off',
            'Block delivery until both approve',
          ],
          dataFlow: ['CompliantCommentary → edits → approvals', 'Delivery unlocked on dual approval'],
          technologies: ['React', 'FastAPI', 'Azure Cosmos DB'],
          keyFacts: ['AI drafts; humans remain accountable'],
        },
      },
      {
        id: 'delivered',
        type: 'outcome',
        label: 'Delivered / Exported',
        subtitle: 'outcome · PDF / Word / Email / portal',
        position: { x: 310, y: 840 },
        detail: {
          title: 'Delivered / Exported Commentary',
          subtitle: 'outcome · PDF / Word / Email / portal',
          description:
            'The approved, compliant, fully-sourced commentary — delivered to the client and ' +
            'exportable as PDF, Word, or a ready-to-send email. Every export is audit-logged.',
          sourceFiles: [
            'backend/app/routers/approvals.py',
            'backend/app/routers/export.py',
            'backend/app/services/export.py',
          ],
          responsibilities: [
            'Deliver only after dual approval',
            'Export to PDF (reportlab) / Word (python-docx) / .eml',
            'Record delivery and every export in the audit trail',
          ],
          dataFlow: ['Approved commentary → delivery channel', 'Approved commentary → PDF/DOCX/EML'],
          technologies: ['FastAPI', 'reportlab', 'python-docx'],
        },
      },
    ],
    edges: [
      { id: 'e1', source: 'doc-intel', target: 'pdf-index' },
      { id: 'e2', source: 'pdf-index', target: 'foundry-iq' },
      { id: 'e3', source: 'foundry-iq', target: 'portfolio' },
      { id: 'e4', source: 'foundry-iq', target: 'narrative' },
      { id: 'er1', source: 'refdata', target: 'portfolio', label: 'local mode' },
      { id: 'er2', source: 'refdata', target: 'market', label: 'local mode' },
      { id: 'e5', source: 'portfolio', target: 'narrative' },
      { id: 'e6', source: 'market', target: 'narrative' },
      { id: 'e7', source: 'narrative', target: 'substantiation' },
      { id: 'e7b', source: 'substantiation', target: 'compliance' },
      { id: 'e8', source: 'compliance', target: 'store' },
      { id: 'e9', source: 'store', target: 'gate' },
      { id: 'e10', source: 'gate', target: 'delivered' },
    ],
  },
  {
    id: 'research-mcp',
    label: 'Research & Market Data (MCP)',
    description:
      'On-demand third-party research and market data via provider MCP servers (Morningstar, ' +
      'LSEG). A one-time interactive OAuth login stores a refresh token; the backend mints access ' +
      'tokens headlessly and the Foundry LLM orchestrates the provider tools executed over a ' +
      'direct MCP client. No numbers are fabricated — every figure is attributed to the provider.',
    nodes: [
      {
        id: 'r-refdata',
        type: 'datastore',
        label: 'Reference Dataset',
        subtitle: 'datastore · reference_data.py',
        position: { x: 40, y: 40 },
        detail: {
          title: 'Reference Dataset',
          subtitle: 'datastore · reference_data.py',
          description:
            'Supplies the mandate holdings (tickers + ISINs + weights) that seed the Morningstar ' +
            'X-Ray and the sector/benchmark focus for the LSEG market context.',
          sourceFiles: ['backend/app/services/reference_data.py'],
          responsibilities: [
            'Provide holdings (ISIN/ticker/weight) for X-Ray',
            'Provide benchmark + sectors for market context',
          ],
          dataFlow: ['Holdings + mandate → research prompts'],
          technologies: ['Real ETF/equity identifiers'],
        },
      },
      {
        id: 'r-oauth',
        type: 'service',
        label: 'MCP OAuth',
        subtitle: 'service · mcp_oauth.py',
        position: { x: 40, y: 180 },
        detail: {
          title: 'MCP OAuth (authorization_code + refresh)',
          subtitle: 'service · mcp_oauth.py',
          description:
            'RFC 9728 discovery (via the MCP 401 WWW-Authenticate challenge), dynamic or ' +
            'pre-registered client, PKCE authorization-code login (one-time, browser), and headless ' +
            'refresh-token → access-token exchange. Tokens stored under data/oauth (gitignored).',
          sourceFiles: [
            'backend/app/services/mcp_oauth.py',
            'backend/scripts/mcp_login.py',
          ],
          responsibilities: [
            'Discover the provider authorization server',
            'One-time interactive login → refresh token',
            'Mint short-lived access tokens on each request',
          ],
          dataFlow: [
            'MCP 401 → resource metadata → auth server',
            'refresh_token → access_token (bearer)',
          ],
          technologies: ['OAuth 2.1', 'PKCE (S256)', 'RFC 8414 / 9728'],
          keyFacts: ['Headless after a one-time browser login; no user needed at request time'],
        },
      },
      {
        id: 'r-agent',
        type: 'agent',
        label: 'ResearchAgent',
        subtitle: 'agent · research_agent.py / research_direct.py',
        position: { x: 300, y: 180 },
        detail: {
          title: 'ResearchAgent (LLM function-bridge)',
          subtitle: 'agent · research_agent.py / research_direct.py',
          description:
            'The Foundry LLM is given the provider MCP tools as function definitions and decides ' +
            'which to call; each call is executed over the direct MCP client with the bearer token. ' +
            'Returns a grounded, provider-attributed answer with citations.',
          sourceFiles: [
            'backend/app/agents/research_agent.py',
            'backend/app/services/research_direct.py',
            'backend/app/routers/research.py',
          ],
          responsibilities: [
            'List provider tools and expose them to the LLM',
            'Run the tool-calling loop (portfolio X-Ray, market context)',
            'Return answer + citations; 503 until the provider is logged in',
          ],
          dataFlow: [
            'tools/list → OpenAI function tools',
            'LLM tool calls → MCP tools/call → results → answer',
          ],
          technologies: ['Foundry LLM (chat4o)', 'OpenAI function calling'],
        },
      },
      {
        id: 'r-client',
        type: 'service',
        label: 'MCP Client',
        subtitle: 'service · mcp_client.py',
        position: { x: 300, y: 40 },
        detail: {
          title: 'MCP Streamable-HTTP Client',
          subtitle: 'service · mcp_client.py',
          description:
            'Minimal JSON-RPC 2.0 MCP client: initialize → tools/list → tools/call over HTTP, ' +
            'handling JSON and SSE responses, the Mcp-Session-Id header, and the bearer token.',
          sourceFiles: ['backend/app/services/mcp_client.py'],
          responsibilities: [
            'MCP handshake + session management',
            'Execute tools/call with the OAuth bearer token',
          ],
          dataFlow: ['initialize / tools/list / tools/call → provider MCP'],
          technologies: ['MCP Streamable HTTP', 'JSON-RPC 2.0', 'httpx'],
        },
      },
      {
        id: 'r-morningstar',
        type: 'service',
        label: 'Morningstar MCP',
        subtitle: 'service · mcp.morningstar.com',
        position: { x: 560, y: 40 },
        detail: {
          title: 'Morningstar MCP Server',
          subtitle: 'service · https://mcp.morningstar.com/mcp',
          description:
            'Provider MCP server exposing analyst research, data, fund holdings, and the portfolio ' +
            'X-Ray (asset allocation, sector, region, style, risk/return). OAuth authorization_code.',
          sourceFiles: [],
          responsibilities: [
            'Resolve securities by ISIN/ticker (id-lookup)',
            'Run portfolio X-Ray on resolvable holdings',
          ],
          dataFlow: ['Holdings → X-Ray → allocation / style / risk'],
          technologies: ['Morningstar MCP', 'OAuth 2.1'],
        },
      },
      {
        id: 'r-lseg',
        type: 'service',
        label: 'LSEG MCP',
        subtitle: 'service · api.analytics.lseg.com',
        position: { x: 560, y: 180 },
        detail: {
          title: 'LSEG MCP Server',
          subtitle: 'service · https://api.analytics.lseg.com/lfa/mcp',
          description:
            'Provider MCP server for market data and analytics (index returns, yield curve, FX, ' +
            'macro themes). Auth via Refinitiv CIAM (pre-registered client).',
          sourceFiles: [],
          responsibilities: [
            'Serve index / curve / FX / macro context',
            'Attribute figures to LSEG',
          ],
          dataFlow: ['Period + benchmark → market context'],
          technologies: ['LSEG MCP', 'Refinitiv CIAM OAuth'],
        },
      },
      {
        id: 'r-xray',
        type: 'outcome',
        label: 'Morningstar X-Ray',
        subtitle: 'outcome · Portfolio detail panel',
        position: { x: 300, y: 320 },
        detail: {
          title: 'Morningstar X-Ray',
          subtitle: 'outcome · /mandates/{id}/morningstar-xray',
          description:
            'Independent asset-allocation, sector, region, style, and risk/return analysis of the ' +
            'mandate’s holdings, surfaced on the Portfolio detail page with source citations.',
          sourceFiles: ['frontend/src/components/research/MorningstarXray.tsx'],
          responsibilities: ['Render the X-Ray + citations on demand'],
          dataFlow: ['Answer + citations → Portfolio panel'],
          technologies: ['React'],
        },
      },
      {
        id: 'r-market',
        type: 'outcome',
        label: 'LSEG Market Context',
        subtitle: 'outcome · Portfolio detail panel',
        position: { x: 560, y: 320 },
        detail: {
          title: 'LSEG Market Context',
          subtitle: 'outcome · /mandates/{id}/lseg-context',
          description:
            'Index returns, yield-curve moves, FX, and macro themes for the reporting period, ' +
            'tailored to the mandate benchmark and surfaced on the Portfolio detail page.',
          sourceFiles: ['frontend/src/components/research/LsegMarketContext.tsx'],
          responsibilities: ['Render market context + citations on demand'],
          dataFlow: ['Answer + citations → Portfolio panel'],
          technologies: ['React'],
        },
      },
    ],
    edges: [
      { id: 'r-e1', source: 'r-refdata', target: 'r-agent', label: 'holdings' },
      { id: 'r-e2', source: 'r-oauth', target: 'r-agent', label: 'bearer' },
      { id: 'r-e3', source: 'r-agent', target: 'r-client', label: 'tools/call' },
      { id: 'r-e4', source: 'r-client', target: 'r-morningstar' },
      { id: 'r-e5', source: 'r-client', target: 'r-lseg' },
      { id: 'r-e6', source: 'r-agent', target: 'r-xray' },
      { id: 'r-e7', source: 'r-agent', target: 'r-market' },
    ],
  },
]
