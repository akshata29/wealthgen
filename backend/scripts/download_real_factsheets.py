"""Download real, publicly available fund fact sheets from the manifest.

Reads ``data/real_funds/manifest.json`` and downloads each fund's public
fact-sheet PDF into ``data/real_funds/pdfs/``. These are genuine iShares (public
literature) documents used to ground commentary with real fund facts instead of
synthetic sheets.

Run:
    cd backend
    python -m scripts.download_real_factsheets
    python -m scripts.download_real_factsheets --force   # re-download all
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import urllib.request
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_REAL_ROOT = _BACKEND_ROOT / "data" / "real_funds"
_MANIFEST = _REAL_ROOT / "manifest.json"
_PDF_DIR = _REAL_ROOT / "pdfs"
_USER_AGENT = "Mozilla/5.0 (WealthGen factsheet fetcher)"


def _download(url: str, dest: Path) -> int:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (trusted public URL)
        data = resp.read()
    if not data.startswith(b"%PDF"):
        raise ValueError(f"Downloaded content from {url} is not a PDF.")
    dest.write_bytes(data)
    return len(data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Re-download even if present.")
    args = parser.parse_args()

    manifest = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    _PDF_DIR.mkdir(parents=True, exist_ok=True)

    ok = 0
    for fund in manifest.get("funds", []):
        dest = _PDF_DIR / fund["pdf"]
        if dest.exists() and not args.force:
            logger.info("%s already present (%d bytes).", fund["pdf"], dest.stat().st_size)
            ok += 1
            continue
        try:
            size = _download(fund["factsheet_url"], dest)
            logger.info("%s <- %s (%d bytes)", fund["pdf"], fund["ticker"], size)
            ok += 1
        except Exception as exc:  # noqa: BLE001 (report and continue)
            logger.error("FAILED %s: %s", fund["ticker"], exc)

    logger.info("Done: %d/%d fact sheets available in %s", ok, len(manifest.get("funds", [])), _PDF_DIR)


if __name__ == "__main__":
    main()
