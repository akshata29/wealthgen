"""Microsoft Fabric Warehouse data provider (reference dataset over OneLake).

Reads the advisory reference tables (clients, mandates, holdings, attribution,
performance, market context) from a Fabric **Warehouse** through its SQL analytics
endpoint, using AAD token authentication (no SQL login, no stored secret).

Rows are returned as ``dict[str, str | None]`` keyed by column name, with values
normalised to strings so the ``reference_data._to_*`` mappers stay byte-for-byte
compatible with the CSV provider (booleans map to ``"True"``/``"False"`` exactly
as the CSVs do).

Selected only when ``DATA_SOURCE_MODE=fabric``. Requires the Microsoft ODBC Driver
18 for SQL Server on the host and ``FABRIC_SQL_ENDPOINT`` / ``FABRIC_DATABASE`` set.
"""

from __future__ import annotations

import logging
import re
import struct
from decimal import Decimal

from app.infra.clients import get_credential
from app.infra.settings import get_settings

logger = logging.getLogger(__name__)

# ODBC connection attribute for AAD access-token auth (mssql-specific).
_SQL_COPT_SS_ACCESS_TOKEN = 1256
# Scope for the Fabric/SQL data-plane token.
_DB_SCOPE = "https://database.windows.net/.default"
# Identifier allow-list — table/schema names are code-controlled, but validate anyway.
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Module-scoped cached connection (reconnected on pyodbc.Error).
_conn = None


class FabricDataError(RuntimeError):
    """Raised when the Fabric Warehouse endpoint is unreachable or a table is missing."""


def _safe_identifier(name: str) -> str:
    if not _IDENTIFIER.match(name):
        raise FabricDataError(f"Invalid SQL identifier: {name!r}")
    return name


def _access_token_struct() -> bytes:
    """Encode an AAD access token in the packed form ODBC expects."""
    token = get_credential().get_token(_DB_SCOPE).token
    token_bytes = token.encode("UTF-16-LE")
    return struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)


def _connect():
    """Open (or reuse) a pyodbc connection to the Fabric Warehouse SQL endpoint."""
    global _conn
    if _conn is not None:
        return _conn

    try:
        import pyodbc
    except ImportError as exc:  # pragma: no cover - environment guard
        raise FabricDataError(
            "pyodbc is not installed. Install it and the Microsoft ODBC Driver 18 "
            "for SQL Server (see backend/scripts/fabric/README.md)."
        ) from exc

    settings = get_settings()
    if not (settings.fabric_sql_endpoint and settings.fabric_database):
        raise FabricDataError(
            "FABRIC_SQL_ENDPOINT and FABRIC_DATABASE must be set for DATA_SOURCE_MODE=fabric."
        )

    conn_str = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server={settings.fabric_sql_endpoint},1433;"
        f"Database={settings.fabric_database};"
        "Encrypt=yes;TrustServerCertificate=no"
    )
    # Log host + database only — never the token or full connection string.
    logger.info(
        "Connecting to Fabric Warehouse (server=%s database=%s)",
        settings.fabric_sql_endpoint,
        settings.fabric_database,
    )
    try:
        _conn = pyodbc.connect(
            conn_str, attrs_before={_SQL_COPT_SS_ACCESS_TOKEN: _access_token_struct()}
        )
    except pyodbc.Error as exc:  # pragma: no cover - network path
        raise FabricDataError(
            "Could not connect to the Fabric Warehouse SQL endpoint. Verify "
            "FABRIC_SQL_ENDPOINT/FABRIC_DATABASE, that the identity has Warehouse "
            "access, and that ODBC Driver 18 for SQL Server is installed."
        ) from exc
    return _conn


def _normalize(value: object) -> str | None:
    """Coerce a SQL value to the string form the CSV mappers expect.

    ``None`` stays ``None``; ``bool`` -> ``"True"``/``"False"`` (matching the CSVs);
    ``Decimal``/``float``/``int`` -> ``str`` (mappers coerce via ``float()``).
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (Decimal, float, int)):
        return str(value)
    return str(value)


def query(sql: str, params: tuple = ()) -> list[dict]:
    """Run a read query and return rows as column-keyed string dicts."""
    import pyodbc  # local import so module loads without the driver present

    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        rows = [
            {col: _normalize(val) for col, val in zip(columns, record)}
            for record in cursor.fetchall()
        ]
        cursor.close()
        return rows
    except pyodbc.Error as exc:
        # Drop the cached connection so the next call reconnects cleanly.
        global _conn
        _conn = None
        raise FabricDataError(
            "Fabric Warehouse query failed. Check that the reference tables have "
            "been loaded (backend/scripts/load_fabric_tables.py) and the endpoint "
            "is reachable."
        ) from exc


def read_table(name: str) -> list[dict]:
    """Read every row of a reference table (``SELECT * FROM <schema>.<name>``)."""
    settings = get_settings()
    schema = _safe_identifier(settings.fabric_sql_schema)
    table = _safe_identifier(name)
    return query(f"SELECT * FROM {schema}.{table}")


# --------------------------------------------------------------------------- #
# Catalog-equivalent helpers (replacing catalog.json reads)
# --------------------------------------------------------------------------- #
def read_clients() -> list[dict]:
    return read_table("clients")


def read_mandates() -> list[dict]:
    return read_table("mandates")


def read_advisors() -> list[dict]:
    return read_table("advisors")


def read_periods() -> list[str]:
    settings = get_settings()
    schema = _safe_identifier(settings.fabric_sql_schema)
    # Order chronologically (period is "Q<n>-YYYY"): by year, then quarter. GROUP BY
    # (not SELECT DISTINCT) so the ORDER BY expressions may reference the grouped
    # column — a plain ORDER BY period would sort alphabetically and break latest_period().
    rows = query(
        f"SELECT period FROM {schema}.portfolio_performance "
        "GROUP BY period ORDER BY RIGHT(period, 4), LEFT(period, 2)"
    )
    return [row["period"] for row in rows if row["period"] is not None]
