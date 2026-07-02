"""Direct research via provider MCP servers (headless, OAuth refresh-token path).

Bridges the Foundry LLM (function calling) to a provider's MCP tools that we
execute ourselves over HTTP with a bearer token minted from the stored refresh
token (see mcp_oauth). This makes the research agent work headlessly — no Foundry
project connection and no interactive user required at request time.

Flow: mint access token -> MCP initialize + tools/list -> expose tools to the LLM
as functions -> run the tool-calling loop, executing each call via MCPClient.
"""

from __future__ import annotations

import json
import logging

from app.agents.prompts import RESEARCH_SYSTEM
from app.infra.clients import get_project_client
from app.infra.settings import get_settings
from app.models.sources import Citation
from app.services import mcp_oauth
from app.services.mcp_client import MCPClient

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 6


def _openai_tools(mcp_tools: list[dict]) -> list[dict]:
    """Convert MCP tool descriptors into OpenAI function-tool definitions."""
    tools: list[dict] = []
    for t in mcp_tools:
        schema = t.get("inputSchema") or {"type": "object", "properties": {}}
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": (t.get("description") or "")[:1024],
                    "parameters": schema,
                },
            }
        )
    return tools


def _tool_result_text(result: dict) -> str:
    """Flatten an MCP tools/call result into text for the LLM."""
    parts: list[str] = []
    for item in result.get("content", []) or []:
        if item.get("type") == "text" and item.get("text"):
            parts.append(item["text"])
    if not parts and result.get("structuredContent"):
        parts.append(json.dumps(result["structuredContent"]))
    return "\n".join(parts) if parts else json.dumps(result)[:4000]


async def run(provider: str, query: str) -> tuple[str, list[Citation]]:
    """Answer a query using the provider's MCP tools, orchestrated by the LLM."""
    settings = get_settings()
    token = mcp_oauth.get_access_token(provider)
    record = mcp_oauth.load_tokens(provider)
    endpoint = record["mcp_url"]

    openai_client = get_project_client().get_openai_client()
    used_tools: set[str] = set()

    async with MCPClient(endpoint, token) as mcp:
        mcp_tools = await mcp.list_tools()
        if not mcp_tools:
            raise RuntimeError(f"{provider} MCP server exposed no tools.")
        tools = _openai_tools(mcp_tools)

        messages: list[dict] = [
            {"role": "system", "content": RESEARCH_SYSTEM},
            {"role": "user", "content": query},
        ]

        for _ in range(MAX_TOOL_ROUNDS):
            completion = openai_client.chat.completions.create(
                model=settings.agent_model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
            msg = completion.choices[0].message
            if not msg.tool_calls:
                citations = [
                    Citation(source_id=f"{provider}:{name}", display=f"{provider} · {name}")
                    for name in sorted(used_tools)
                ]
                return msg.content or "", citations

            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                        }
                        for tc in msg.tool_calls
                    ],
                }
            )
            for tc in msg.tool_calls:
                used_tools.add(tc.function.name)
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = await mcp.call_tool(tc.function.name, args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": _tool_result_text(result),
                    }
                )

    # Ran out of rounds — return best-effort with a note.
    return "Reached the tool-call limit before a final answer.", []
