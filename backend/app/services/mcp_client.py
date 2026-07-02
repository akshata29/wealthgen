"""Minimal MCP client over the Streamable HTTP transport.

Speaks JSON-RPC 2.0 to an MCP server endpoint (e.g. Morningstar's
https://mcp.morningstar.com/mcp) with a bearer access token. Supports the subset
we need: initialize -> tools/list -> tools/call. Handles both application/json and
text/event-stream (SSE) responses and the Mcp-Session-Id header.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

PROTOCOL_VERSION = "2025-06-18"
_CLIENT_INFO = {"name": "wealthgen-research", "version": "1.0.0"}


class MCPError(RuntimeError):
    """An MCP JSON-RPC error or transport failure."""


class MCPClient:
    def __init__(self, endpoint: str, access_token: str, timeout: float = 120.0) -> None:
        self._endpoint = endpoint
        self._token = access_token
        self._timeout = timeout
        self._session_id: str | None = None
        self._id = 0
        self._client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self) -> "MCPClient":
        await self.initialize()
        return self

    async def __aexit__(self, *exc) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": PROTOCOL_VERSION,
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        return headers

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    @staticmethod
    def _parse(resp: httpx.Response) -> dict | None:
        """Return the JSON-RPC message from a JSON or SSE response body."""
        ctype = resp.headers.get("content-type", "")
        if "text/event-stream" in ctype:
            for line in resp.text.splitlines():
                line = line.strip()
                if line.startswith("data:"):
                    payload = line[len("data:"):].strip()
                    if payload and payload != "[DONE]":
                        return json.loads(payload)
            return None
        if not resp.text:
            return None
        return resp.json()

    async def _request(self, method: str, params: dict | None = None) -> Any:
        payload = {"jsonrpc": "2.0", "id": self._next_id(), "method": method}
        if params is not None:
            payload["params"] = params
        resp = await self._client.post(self._endpoint, headers=self._headers(), json=payload)
        if resp.status_code >= 400:
            raise MCPError(f"{method} failed ({resp.status_code}): {resp.text[:500]}")
        if not self._session_id and resp.headers.get("mcp-session-id"):
            self._session_id = resp.headers["mcp-session-id"]
        message = self._parse(resp)
        if message is None:
            raise MCPError(f"{method}: empty response.")
        if "error" in message:
            raise MCPError(f"{method}: {message['error']}")
        return message.get("result")

    async def _notify(self, method: str, params: dict | None = None) -> None:
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        await self._client.post(self._endpoint, headers=self._headers(), json=payload)

    async def initialize(self) -> dict:
        result = await self._request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": _CLIENT_INFO,
            },
        )
        await self._notify("notifications/initialized")
        return result or {}

    async def list_tools(self) -> list[dict]:
        result = await self._request("tools/list")
        return (result or {}).get("tools", [])

    async def call_tool(self, name: str, arguments: dict | None = None) -> dict:
        return await self._request("tools/call", {"name": name, "arguments": arguments or {}})
