"""One-time interactive OAuth login for an MCP provider.

Runs the authorization_code + PKCE flow in your browser, captures the redirect,
exchanges the code for tokens, and stores the refresh_token so the backend can
call the provider's MCP server headlessly (see app/services/mcp_oauth.py).

Usage:
    cd backend
    python -m scripts.mcp_login morningstar
    python -m scripts.mcp_login lseg --mcp-url https://api.analytics.lseg.com/lfa/mcp

Provider -> MCP URL defaults are read from settings; override with --mcp-url.
"""

from __future__ import annotations

import argparse
import logging
import os
import secrets
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

from dotenv import load_dotenv

from app.infra.settings import get_settings
from app.services import mcp_oauth

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

REDIRECT_PORT = 8765
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"
CLIENT_NAME = "WealthGen Research"


class _CallbackHandler(BaseHTTPRequestHandler):
    code: str | None = None
    state: str | None = None

    def do_GET(self) -> None:  # noqa: N802 - required name
        query = parse_qs(urlsplit(self.path).query)
        _CallbackHandler.code = (query.get("code") or [None])[0]
        _CallbackHandler.state = (query.get("state") or [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        body = (
            "<html><body style='font-family:sans-serif'>"
            "<h3>Login complete.</h3><p>You can close this tab and return to the terminal.</p>"
            "</body></html>"
        )
        self.wfile.write(body.encode())

    def log_message(self, *args) -> None:  # silence default logging
        return


def _default_mcp_url(provider: str) -> str | None:
    settings = get_settings()
    return {
        "morningstar": settings.morningstar_mcp_url,
        "lseg": settings.lseg_mcp_url,
    }.get(provider)


def login(
    provider: str,
    mcp_url: str,
    client_id: str | None = None,
    client_secret: str | None = None,
    redirect_uri: str = REDIRECT_URI,
) -> None:
    logger.info("Discovering OAuth metadata for %s (%s)...", provider, mcp_url)
    meta = mcp_oauth.discover(mcp_url)
    logger.info("  authorization: %s", meta.authorization_endpoint)
    logger.info("  token:         %s", meta.token_endpoint)

    if client_id:
        logger.info("Using pre-registered client_id: %s", client_id)
    else:
        logger.info("Registering client (dynamic)...")
        try:
            client_id, client_secret = mcp_oauth.register_client(meta, redirect_uri, CLIENT_NAME)
            logger.info("  client_id: %s", client_id)
        except Exception as exc:  # noqa: BLE001 - give an actionable hint
            raise mcp_oauth.OAuthError(
                f"Dynamic client registration failed ({exc}). This provider likely requires a "
                f"pre-registered client. Set {provider.upper()}_CLIENT_ID (and "
                f"{provider.upper()}_CLIENT_SECRET) in .env, or pass --client-id / --client-secret, "
                "and ensure the redirect URI is allow-listed for that client."
            ) from exc

    verifier, challenge = mcp_oauth.pkce_pair()
    state = secrets.token_urlsafe(16)
    scope = " ".join(meta.scopes_supported)
    auth_url = mcp_oauth.build_authorization_url(
        meta, client_id, redirect_uri, scope, state, challenge
    )

    port = urlsplit(redirect_uri).port or REDIRECT_PORT
    logger.info("Opening browser to sign in. If it does not open, visit:\n%s", auth_url)
    server = HTTPServer(("localhost", port), _CallbackHandler)
    webbrowser.open(auth_url)
    logger.info("Waiting for the redirect on %s ...", redirect_uri)
    server.handle_request()  # blocks until the browser hits /callback

    if not _CallbackHandler.code:
        raise mcp_oauth.OAuthError("No authorization code received.")
    if _CallbackHandler.state != state:
        raise mcp_oauth.OAuthError("State mismatch — possible CSRF; aborting.")

    logger.info("Exchanging authorization code for tokens...")
    tok = mcp_oauth.exchange_code(
        meta, client_id, client_secret, _CallbackHandler.code, redirect_uri, verifier
    )
    if not tok.get("refresh_token"):
        logger.warning(
            "No refresh_token returned — the provider may not have granted offline_access. "
            "Headless refresh will not be possible."
        )

    mcp_oauth.save_tokens(
        provider,
        {
            "provider": provider,
            "mcp_url": mcp_url,
            "token_endpoint": meta.token_endpoint,
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": tok.get("refresh_token"),
            "access_token": tok.get("access_token"),
            "expires_at": time.time() + int(tok.get("expires_in", 3600)),
            "scope": tok.get("scope", scope),
        },
    )
    logger.info("Done. Stored tokens for '%s'. The backend can now call it headlessly.", provider)


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="One-time MCP OAuth login.")
    parser.add_argument("provider", help="Provider key, e.g. 'morningstar' or 'lseg'.")
    parser.add_argument("--mcp-url", default=None, help="Override the MCP endpoint URL.")
    parser.add_argument("--client-id", default=None, help="Pre-registered OAuth client id.")
    parser.add_argument("--client-secret", default=None, help="Pre-registered OAuth client secret.")
    parser.add_argument(
        "--redirect-uri", default=REDIRECT_URI, help=f"OAuth redirect URI (default {REDIRECT_URI})."
    )
    args = parser.parse_args()

    mcp_url = args.mcp_url or _default_mcp_url(args.provider)
    if not mcp_url:
        raise SystemExit(f"No MCP URL for '{args.provider}'. Pass --mcp-url.")

    prefix = args.provider.upper()
    client_id = args.client_id or os.environ.get(f"{prefix}_CLIENT_ID")
    client_secret = args.client_secret or os.environ.get(f"{prefix}_CLIENT_SECRET")
    login(args.provider, mcp_url, client_id, client_secret, args.redirect_uri)


if __name__ == "__main__":
    main()
