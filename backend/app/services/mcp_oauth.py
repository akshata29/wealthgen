"""OAuth 2.1 client for MCP servers (authorization_code + PKCE + refresh_token).

Providers like Morningstar expose an OAuth authorization server (discoverable at
`/.well-known/oauth-authorization-server`) that only supports the interactive
`authorization_code` grant plus `refresh_token`. There is NO password/client-
credentials grant, so a headless service must:

  1. run a ONE-TIME interactive login (see scripts/mcp_login.py) to capture a
     long-lived refresh_token (scope `offline_access`), stored on disk; then
  2. at runtime, exchange that refresh_token for short-lived access tokens here.

Token store: backend/data/oauth/<provider>.json  (gitignored — contains secrets).
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import secrets
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

_TOKEN_DIR = Path(__file__).resolve().parents[2] / "data" / "oauth"
_ACCESS_TOKEN_SKEW_SECONDS = 60


class OAuthError(RuntimeError):
    """OAuth flow or token-refresh failure."""


class NotLoggedInError(OAuthError):
    """No stored refresh token for the provider — run the one-time login."""


@dataclass(frozen=True)
class ProviderMetadata:
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    registration_endpoint: str | None
    scopes_supported: list[str]


def _origin(url: str) -> str:
    # https://mcp.morningstar.com/mcp -> https://mcp.morningstar.com
    from urllib.parse import urlsplit

    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


def discover(mcp_url: str) -> ProviderMetadata:
    """Fetch OAuth authorization-server metadata for an MCP endpoint.

    Discovery order:
      1. RFC 9728: read the MCP endpoint's 401 `WWW-Authenticate` header for a
         `resource_metadata_uri`, fetch the protected-resource metadata, then the
         authorization server's metadata (this is how LSEG/Refinitiv CIAM works).
      2. Protected-resource metadata at the standard well-known paths.
      3. RFC 8414 authorization-server metadata at the origin / MCP path
         (this is how Morningstar works).
    """
    origin = _origin(mcp_url)
    base = mcp_url.rstrip("/")

    prm_urls = [
        _resource_metadata_uri(mcp_url),
        f"{base}/.well-known/oauth-protected-resource",
        f"{origin}/.well-known/oauth-protected-resource",
    ]
    for url in prm_urls:
        if not url:
            continue
        data = _try_get_json(url)
        for server in (data or {}).get("authorization_servers", []) or []:
            meta = _try_get_json(f"{server.rstrip('/')}/.well-known/oauth-authorization-server")
            if meta and "token_endpoint" in meta:
                return _parse_as(meta)

    for url in (
        f"{origin}/.well-known/oauth-authorization-server",
        f"{base}/.well-known/oauth-authorization-server",
    ):
        data = _try_get_json(url)
        if data and "token_endpoint" in data:
            return _parse_as(data)

    raise OAuthError(
        f"Could not discover OAuth metadata for {mcp_url}. Provide the provider's auth docs."
    )


def _resource_metadata_uri(mcp_url: str) -> str | None:
    """Read the RFC 9728 `resource_metadata_uri` from the MCP 401 challenge."""
    import re

    try:
        resp = httpx.get(mcp_url, timeout=20)
    except httpx.HTTPError:
        return None
    challenge = resp.headers.get("www-authenticate", "")
    match = re.search(r'resource_metadata_uri="([^"]+)"', challenge)
    return match.group(1) if match else None


def _try_get_json(url: str) -> dict | None:
    try:
        resp = httpx.get(url, timeout=20)
    except httpx.HTTPError:
        return None
    if resp.status_code == 200:
        try:
            return resp.json()
        except ValueError:
            return None
    return None


def _parse_as(data: dict) -> ProviderMetadata:
    return ProviderMetadata(
        issuer=data["issuer"],
        authorization_endpoint=data["authorization_endpoint"],
        token_endpoint=data["token_endpoint"],
        registration_endpoint=data.get("registration_endpoint"),
        scopes_supported=data.get("scopes_supported", ["offline_access", "openid"]),
    )


def register_client(meta: ProviderMetadata, redirect_uri: str, client_name: str) -> tuple[str, str | None]:
    """Dynamically register a client (RFC 7591). Returns (client_id, client_secret|None)."""
    if not meta.registration_endpoint:
        raise OAuthError("Provider does not support dynamic client registration.")
    body = {
        "client_name": client_name,
        "redirect_uris": [redirect_uri],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "client_secret_post",
        "scope": " ".join(meta.scopes_supported),
    }
    resp = httpx.post(meta.registration_endpoint, json=body, timeout=20)
    resp.raise_for_status()
    reg = resp.json()
    return reg["client_id"], reg.get("client_secret")


def pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) using S256."""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def build_authorization_url(
    meta: ProviderMetadata,
    client_id: str,
    redirect_uri: str,
    scope: str,
    state: str,
    code_challenge: str,
) -> str:
    from urllib.parse import urlencode

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{meta.authorization_endpoint}?{urlencode(params)}"


def exchange_code(
    meta: ProviderMetadata,
    client_id: str,
    client_secret: str | None,
    code: str,
    redirect_uri: str,
    code_verifier: str,
) -> dict:
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "code_verifier": code_verifier,
    }
    if client_secret:
        data["client_secret"] = client_secret
    resp = httpx.post(meta.token_endpoint, data=data, timeout=30)
    if resp.status_code >= 400:
        raise OAuthError(f"Token exchange failed ({resp.status_code}): {resp.text}")
    return resp.json()


def _refresh(token_endpoint: str, client_id: str, client_secret: str | None, refresh_token: str) -> dict:
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
    }
    if client_secret:
        data["client_secret"] = client_secret
    resp = httpx.post(token_endpoint, data=data, timeout=30)
    if resp.status_code >= 400:
        raise OAuthError(f"Token refresh failed ({resp.status_code}): {resp.text}")
    return resp.json()


# --------------------------------------------------------------------------- #
# Token store
# --------------------------------------------------------------------------- #
def _store_path(provider: str) -> Path:
    return _TOKEN_DIR / f"{provider}.json"


def has_login(provider: str) -> bool:
    """True if a stored login (refresh token) exists for the provider."""
    return _store_path(provider).exists()


def save_tokens(provider: str, record: dict) -> None:
    _TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    _store_path(provider).write_text(json.dumps(record, indent=2), encoding="utf-8")
    logger.info("Saved OAuth tokens for '%s'.", provider)


def load_tokens(provider: str) -> dict:
    path = _store_path(provider)
    if not path.exists():
        raise NotLoggedInError(
            f"No stored login for '{provider}'. Run: python -m scripts.mcp_login {provider}"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def get_access_token(provider: str) -> str:
    """Return a valid access token, refreshing via the stored refresh_token if needed."""
    record = load_tokens(provider)
    now = time.time()
    if record.get("access_token") and record.get("expires_at", 0) > now + _ACCESS_TOKEN_SKEW_SECONDS:
        return record["access_token"]

    refresh_token = record.get("refresh_token")
    if not refresh_token:
        raise NotLoggedInError(
            f"No refresh_token for '{provider}'. Re-run: python -m scripts.mcp_login {provider}"
        )
    tok = _refresh(
        record["token_endpoint"], record["client_id"], record.get("client_secret"), refresh_token
    )
    record["access_token"] = tok["access_token"]
    record["expires_at"] = now + int(tok.get("expires_in", 3600))
    if tok.get("refresh_token"):  # rotating refresh tokens
        record["refresh_token"] = tok["refresh_token"]
    save_tokens(provider, record)
    return record["access_token"]
