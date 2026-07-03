"""Load the synthetic reference CSVs into a Microsoft Fabric Warehouse.

One-shot, idempotent loader: applies `scripts/fabric/schema.sql` (create-if-missing)
then batch-inserts each `data/synthetic/fabric_iq/*.csv` into the matching Warehouse
table through the Fabric SQL analytics endpoint — pure T-SQL, no notebook or OneLake
file upload. Auth uses the same AAD token path as the runtime provider
(`app.services.fabric_data`); no SQL login or stored secret.

Requires `DATA_SOURCE_MODE=fabric`, `FABRIC_SQL_ENDPOINT`, `FABRIC_DATABASE`, and the
Microsoft ODBC Driver 18 for SQL Server (see scripts/fabric/README.md).

Run:
    cd backend
    python -m scripts.synthetic.generate         # produce data/synthetic/** (if absent)
    python -m scripts.load_fabric_tables          # create tables + load all 11
    python -m scripts.load_fabric_tables --truncate   # TRUNCATE then reload
"""

from __future__ import annotations

import argparse
import csv
import logging
from pathlib import Path

from app.infra.settings import get_settings
from app.services import fabric_data

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# scripts/load_fabric_tables.py -> parents[1] == backend/
_FABRIC_CSV = Path(__file__).resolve().parents[1] / "data" / "synthetic" / "fabric_iq"
_SCHEMA_SQL = Path(__file__).resolve().parent / "fabric" / "schema.sql"

# Load order (no FKs declared; order is cosmetic).
_TABLES = [
    "advisors",
    "clients",
    "mandates",
    "benchmarks",
    "holdings",
    "portfolio_performance",
    "attribution",
    "positioning_changes",
    "market_index_returns",
    "fx_moves",
    "vix_events",
]

# Column-name -> value kind (everything else is treated as a string).
_FLOAT_COLS = {
    "weight", "aum_musd", "market_value_usd", "period_return_pct",
    "total_return_net_pct", "benchmark_return_pct", "active_return_bps",
    "tracking_error_pct", "information_ratio", "ex_ante_vol_pct", "sharpe",
    "max_drawdown_pct", "portfolio_weight", "benchmark_weight",
    "portfolio_return", "benchmark_return", "allocation_bps", "selection_bps",
    "interaction_bps", "change_pct", "vix_close",
}
_BOOL_COLS = {"esg_preference", "event_trigger"}


def _coerce(column: str, value: str):
    """Coerce a CSV cell to the Python type the target column expects."""
    if value == "":
        return None
    if column in _BOOL_COLS:
        return 1 if value.strip().lower() in ("true", "1") else 0
    if column in _FLOAT_COLS:
        return float(value)
    return value


def _apply_schema(cursor, schema: str) -> None:
    ddl = _SCHEMA_SQL.read_text(encoding="utf-8").replace("{schema}", schema)
    for statement in (s.strip() for s in ddl.split(";")):
        if statement:
            cursor.execute(statement)
    logger.info("Applied schema.sql (create-if-missing) to schema '%s'.", schema)


def _load_table(cursor, schema: str, table: str, truncate: bool) -> int:
    path = _FABRIC_CSV / f"{table}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run 'python -m scripts.synthetic.generate' first."
        )

    with path.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        columns = reader.fieldnames or []
        rows = [tuple(_coerce(col, row[col]) for col in columns) for row in reader]

    if truncate:
        cursor.execute(f"TRUNCATE TABLE {schema}.{table}")

    if rows:
        placeholders = ", ".join("?" for _ in columns)
        col_list = ", ".join(columns)
        cursor.fast_executemany = True
        cursor.executemany(
            f"INSERT INTO {schema}.{table} ({col_list}) VALUES ({placeholders})", rows
        )
    return len(rows)


def load(truncate: bool = False) -> int:
    settings = get_settings()
    if settings.data_source_mode != "fabric":
        raise RuntimeError(
            "DATA_SOURCE_MODE must be 'fabric' to load the Warehouse "
            f"(current: '{settings.data_source_mode}')."
        )
    schema = settings.fabric_sql_schema
    conn = fabric_data._connect()
    cursor = conn.cursor()

    _apply_schema(cursor, schema)
    conn.commit()

    total = 0
    for table in _TABLES:
        count = _load_table(cursor, schema, table, truncate)
        conn.commit()
        logger.info("  %-24s %d rows", table, count)
        total += count

    cursor.close()
    return total


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load synthetic reference CSVs into a Fabric Warehouse."
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="TRUNCATE each table before loading (idempotent reload).",
    )
    args = parser.parse_args()

    total = load(truncate=args.truncate)
    logger.info("Loaded %d rows into the Fabric Warehouse across %d tables.", total, len(_TABLES))


if __name__ == "__main__":
    main()
