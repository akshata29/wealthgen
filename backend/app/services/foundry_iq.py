"""Foundry IQ — the grounding hub + Foundry agent helpers (new-GA azure-ai-projects 2.x).

A single knowledge base aggregates the PDF index, Work IQ, Fabric IQ, and Web IQ
sources and is exposed to agents as the MCP tool `knowledge_base_retrieve`.
"""

from __future__ import annotations

import logging

from app.infra.clients import get_project_client
from app.infra.settings import get_settings
from app.models.sources import Citation

logger = logging.getLogger(__name__)


def retrieve_grounding(
    query: str, mandate_id: str | None = None, period: str | None = None
) -> tuple[str, list[Citation]]:
    """Retrieve grounded, cited content from the KB, optionally scoped by mandate/period.

    Uses the direct KnowledgeBaseRetrievalClient so retrieval can be hard-filtered
    (via `filter_add_on`) — the agent/MCP path can't scope per query.
    """
    from app.infra.clients import get_kb_retrieval_client
    from azure.search.documents.knowledgebases.models import (
        KnowledgeBaseMessage,
        KnowledgeBaseMessageTextContent,
        KnowledgeBaseRetrievalRequest,
        SearchIndexKnowledgeSourceParams,
    )

    settings = get_settings()
    clauses = []
    if mandate_id:
        clauses.append(f"mandate_id eq '{mandate_id}'")
    if period:
        clauses.append(f"period eq '{period}'")
    filter_add_on = " and ".join(clauses) or None

    request = KnowledgeBaseRetrievalRequest(
        messages=[
            KnowledgeBaseMessage(
                role="user", content=[KnowledgeBaseMessageTextContent(text=query)]
            )
        ],
        knowledge_source_params=[
            SearchIndexKnowledgeSourceParams(
                knowledge_source_name=settings.kb_pdf_source_name,
                filter_add_on=filter_add_on,
            )
        ]
        if filter_add_on
        else None,
    )
    # Fabric Data Agent / ACL sources authorize on behalf of the signed-in user
    # (x-ms-query-source-authorization). Prefer the user's delegated Search token;
    # fall back to the app identity (works for PDF/ACL, but not Fabric Data Agent OBO).
    from app.infra import auth
    from app.infra.clients import get_credential

    qsa = auth.get_user_search_token()
    if not qsa:
        qsa = get_credential().get_token("https://search.azure.com/.default").token
    try:
        response = get_kb_retrieval_client().retrieve(request, query_source_authorization=qsa)
    except Exception as exc:  # noqa: BLE001 — KB answer-synthesis can fail (e.g. reasoning-model incompat)
        # The KB's query-planning/answer-synthesis step depends on the completion
        # model; when that errors, fall back to a direct hybrid search over the
        # same index (proven path) so grounding stays available.
        logger.warning("KB retrieve failed (%s); falling back to direct index search.", exc)
        return _direct_search_grounding(query, filter_add_on)
    text = ""
    for item in response.response or []:
        for content in getattr(item, "content", []) or []:
            text += getattr(content, "text", "") or ""
    return text, _extract_reference_citations(response)


def _extract_reference_citations(response) -> list[Citation]:
    """Parse ref-id references from a KB retrieval response's activity/references."""
    citations: list[Citation] = []
    for ref in getattr(response, "references", []) or []:
        source_id = str(getattr(ref, "source_data", None) or getattr(ref, "id", "source"))
        citations.append(Citation(source_id=source_id, display=source_id, url=None))
    return citations


def _direct_search_grounding(
    query: str, odata_filter: str | None, top: int = 8
) -> tuple[str, list[Citation]]:
    """Hybrid (semantic + vector) search over the PDF index as a KB fallback.

    Assembles grounding text from the top chunk/fact docs and returns per-doc
    citations. Uses the same index the KB wraps, so results stay scoped and cited
    without depending on the KB's completion-model synthesis step.
    """
    from azure.search.documents.models import VectorizableTextQuery

    from app.infra.clients import get_search_client

    client = get_search_client()
    vector_query = VectorizableTextQuery(
        text=query, k_nearest_neighbors=top, fields="content_vector"
    )
    results = client.search(
        search_text=query,
        vector_queries=[vector_query],
        filter=odata_filter,
        top=top,
        select=["id", "content", "label", "section", "source_file", "page", "doc_type"],
    )

    lines: list[str] = []
    citations: list[Citation] = []
    for doc in results:
        content = (doc.get("content") or "").strip()
        if not content:
            continue
        label = doc.get("section") or doc.get("label") or doc.get("source_file") or "source"
        lines.append(f"[{label}] {content}")
        citations.append(
            Citation(source_id=str(doc.get("id", "source")), display=str(label), url=None)
        )
    return "\n\n".join(lines), citations


def run_agent_scoped(
    name: str,
    instructions: str,
    task: str,
    mandate_id: str | None = None,
    period: str | None = None,
    retrieval_query: str | None = None,
) -> tuple[str, list[Citation]]:
    """Run an agent grounded on KB content hard-scoped to mandate/period.

    Pre-retrieves scoped grounding via `retrieve_grounding` (filter_add_on) and
    injects it into the prompt; the agent runs WITHOUT the autonomous KB MCP tool,
    so it can only use the provided (correctly-scoped) context — no cross-quarter bleed.
    """
    grounding, citations = retrieve_grounding(
        retrieval_query or task, mandate_id=mandate_id, period=period
    )
    agent = ensure_agent(name, instructions, tools=[])
    scope = f"(mandate={mandate_id or 'any'}, period={period or 'any'})"
    prompt = (
        f"{task}\n\n"
        f"Use ONLY the grounding below {scope}. Do not use any other data.\n\n"
        f"GROUNDING:\n{grounding}"
    )
    text, _ = run_agent(agent, prompt)
    return text, citations



def build_kb_tool():
    """Return the Foundry IQ knowledge-base MCP tool (verified signature)."""
    from azure.ai.projects.models import MCPTool

    settings = get_settings()
    # The Foundry MCP client needs the token audience as a URL-ENCODED query param
    # on the server URL (raw "https://" breaks query parsing -> "Missing audience").
    server_url = (
        f"{settings.search_endpoint}/knowledgebases/{settings.kb_name}"
        f"/mcp?api-version={settings.kb_mcp_api_version}"
        "&audience=https%3A%2F%2Fsearch.azure.com"
    )
    return MCPTool(
        server_label="knowledge-base",
        server_url=server_url,
        require_approval="never",
        allowed_tools=["knowledge_base_retrieve"],
        project_connection_id=settings.kb_connection_name,
    )


def build_mcp_tool(
    server_label: str,
    connection_name: str,
    server_url: str | None = None,
    allowed_tools: list[str] | None = None,
):
    """Build a generic MCP tool bound to a Foundry project connection.

    The connection (holding the provider's token/OAuth auth) must already exist in
    the project — create it in the Foundry portal (Tools -> add -> authenticate).
    `server_label` must be lowercase alphanumeric/underscore.
    """
    from azure.ai.projects.models import MCPTool

    kwargs: dict = {
        "server_label": server_label,
        "require_approval": "never",
        "project_connection_id": connection_name,
    }
    if server_url:
        kwargs["server_url"] = server_url
    if allowed_tools:
        kwargs["allowed_tools"] = allowed_tools
    return MCPTool(**kwargs)


def ensure_agent(name: str, instructions: str, tools: list | None = None):
    """Create (version) a prompt agent grounded on the Foundry IQ knowledge base."""
    from azure.ai.projects.models import PromptAgentDefinition

    settings = get_settings()
    project = get_project_client()
    return project.agents.create_version(
        agent_name=name,
        definition=PromptAgentDefinition(
            model=settings.agent_model,
            instructions=instructions,
            tools=tools if tools is not None else [build_kb_tool()],
        ),
    )


def run_agent(agent, user_input: str) -> tuple[str, list[Citation]]:
    """Invoke an agent via the Responses API; return (text, citations)."""
    project = get_project_client()
    openai_client = project.get_openai_client()  # not awaited
    conversation = openai_client.conversations.create()
    response = openai_client.responses.create(
        conversation=conversation.id,
        input=user_input,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
    )
    return response.output_text, _extract_citations(response)


def _extract_citations(response) -> list[Citation]:
    """Best-effort parse of URL/source annotations from the Responses output."""
    citations: list[Citation] = []
    try:
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                for ann in getattr(content, "annotations", []) or []:
                    src = getattr(ann, "title", None) or getattr(ann, "source", None) or "source"
                    citations.append(
                        Citation(
                            source_id=str(getattr(ann, "id", src)),
                            display=str(src),
                            url=getattr(ann, "url", None),
                        )
                    )
    except Exception:  # noqa: BLE001 - citation parsing must not break generation
        logger.debug("No parseable citation annotations on response.")
    return citations
