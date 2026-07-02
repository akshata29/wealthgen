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


def build_kb_tool():
    """Return the Foundry IQ knowledge-base MCP tool (verified signature)."""
    from azure.ai.projects.models import MCPTool

    settings = get_settings()
    server_url = (
        f"{settings.search_endpoint}/knowledgebases/{settings.kb_name}"
        f"/mcp?api-version={settings.kb_mcp_api_version}"
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
