"""Per-request user identity for on-behalf-of (OBO) grounding.

Carries the signed-in advisor's Azure AI Search-scoped token through the request
so Foundry IQ retrieval can pass it as `x-ms-query-source-authorization`. The
Fabric Data Agent knowledge source requires this delegated (user) token — the
app's service principal (app-only) token can't be OBO-exchanged to Fabric.

The token is stored in a ContextVar, which propagates through the async request
(and any awaited tasks) without threading it through every function signature.
"""

from __future__ import annotations

import contextvars

_user_search_token: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "user_search_token", default=None
)


def set_user_search_token(token: str | None) -> None:
    """Set the current request's user Search token (None clears it)."""
    _user_search_token.set(token or None)


def get_user_search_token() -> str | None:
    """Return the current request's user Search token, if a user is signed in."""
    return _user_search_token.get()
