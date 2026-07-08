"""Stage the regenerated reference CSVs into the Fabric Lakehouse OneLake Files.

The Lakehouse SQL analytics endpoint is read-only, so the 11 advisory tables are
(re)loaded by the PySpark notebook ``scripts/fabric/load_lakehouse_tables.ipynb``,
which reads ``Files/wealthgen/<table>.csv``. This script uploads those CSVs to
OneLake via the ADLS Gen2 (DFS) API using the app's AAD credential, so after
running it you only need to open the notebook in Fabric and **Run all**.

Requires: DATA_SOURCE_MODE=fabric, FABRIC_WORKSPACE_ID, FABRIC_DATABASE (the
Lakehouse name), and the app identity granted Contributor/Write on the workspace.

Run:
    cd backend
    python -m scripts.stage_lakehouse_csvs
"""

from __future__ import annotations

import json
import logging
import sys
import urllib.request
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from azure.storage.filedatalake import DataLakeServiceClient

from app.infra.clients import get_credential
from app.infra.settings import get_settings

logging.basicConfig(level=logging.INFO, format="%(message)s")
logging.getLogger("azure").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

_ONELAKE_URL = "https://onelake.dfs.fabric.microsoft.com"
_FILES_SUBDIR = "wealthgen"  # matches FILES_DIR = "Files/wealthgen" in the notebook
_CSV_DIR = _BACKEND_ROOT / "data" / "synthetic" / "fabric_iq"

_TABLES = [
    "advisors", "clients", "mandates", "benchmarks", "holdings",
    "portfolio_performance", "attribution", "positioning_changes",
    "market_index_returns", "fx_moves", "vix_events",
]


def _resolve_lakehouse_id(workspace: str, lakehouse_name: str, credential) -> str:
    """Look up the Lakehouse artifact GUID (OneLake rejects friendly names here)."""
    token = credential.get_token("https://api.fabric.microsoft.com/.default").token
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace}/lakehouses"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (trusted Fabric API)
        items = json.loads(resp.read()).get("value", [])
    for item in items:
        if item.get("displayName") == lakehouse_name:
            return item["id"]
    raise SystemExit(
        f"Lakehouse '{lakehouse_name}' not found in workspace {workspace}. "
        f"Available: {[i.get('displayName') for i in items]}"
    )


def main() -> None:
    settings = get_settings()
    workspace = settings.fabric_workspace_id
    lakehouse = settings.fabric_database
    if not workspace or not lakehouse:
        raise SystemExit("FABRIC_WORKSPACE_ID and FABRIC_DATABASE must be set in .env.")

    credential = get_credential()
    lakehouse_id = _resolve_lakehouse_id(workspace, lakehouse, credential)
    logger.info("Resolved Lakehouse '%s' -> %s", lakehouse, lakehouse_id)

    service = DataLakeServiceClient(_ONELAKE_URL, credential=credential)
    file_system = service.get_file_system_client(workspace)
    base = f"{lakehouse_id}/Files/{_FILES_SUBDIR}"
    logger.info("Staging %d CSVs -> %s/%s/", len(_TABLES), workspace, base)

    uploaded = 0
    for table in _TABLES:
        src = _CSV_DIR / f"{table}.csv"
        if not src.exists():
            logger.error("%s missing — run scripts.synthetic.generate first.", src)
            continue
        data = src.read_bytes()
        file_client = file_system.get_file_client(f"{base}/{table}.csv")
        file_client.upload_data(data, overwrite=True)
        logger.info("  %-24s %6d bytes  [OK]", f"{table}.csv", len(data))
        uploaded += 1

    logger.info(
        "Staged %d/%d CSVs. Next: open scripts/fabric/load_lakehouse_tables.ipynb "
        "in Fabric (attach the '%s' Lakehouse) and Run all.",
        uploaded, len(_TABLES), lakehouse,
    )


if __name__ == "__main__":
    main()
