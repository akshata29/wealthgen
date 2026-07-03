"""Unit tests for the Fabric Warehouse data provider (mocked pyodbc)."""

from __future__ import annotations

import logging
import sys
import types

import pytest

from app.services import fabric_data


class _FakePyodbcError(Exception):
    pass


class _FakeCursor:
    def __init__(self, description, rows):
        self.description = description
        self._rows = rows
        self.executed: list[tuple] = []

    def execute(self, sql, params=()):
        self.executed.append((sql, params))

    def fetchall(self):
        return self._rows

    def close(self):
        pass


class _FakeConn:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor


class _FakePyodbc(types.ModuleType):
    Error = _FakePyodbcError

    def __init__(self, cursor=None, raise_on_connect=False):
        super().__init__("pyodbc")
        self._cursor = cursor
        self._raise = raise_on_connect
        self.connect_calls: list[dict] = []

    def connect(self, conn_str, attrs_before=None):
        self.connect_calls.append({"conn_str": conn_str, "attrs_before": attrs_before})
        if self._raise:
            raise _FakePyodbcError("cannot connect")
        return _FakeConn(self._cursor)


class _FakeToken:
    token = "SUPER-SECRET-ACCESS-TOKEN"


class _FakeCredential:
    def get_token(self, scope):
        return _FakeToken()


class _FakeSettings:
    data_source_mode = "fabric"
    fabric_sql_endpoint = "wh123.datawarehouse.fabric.microsoft.com"
    fabric_database = "wealthgen-wh"
    fabric_sql_schema = "dbo"


@pytest.fixture(autouse=True)
def _reset_and_stub(monkeypatch):
    fabric_data._conn = None
    monkeypatch.setattr(fabric_data, "get_settings", lambda: _FakeSettings())
    monkeypatch.setattr(fabric_data, "get_credential", lambda: _FakeCredential())
    yield
    fabric_data._conn = None


def _install_pyodbc(monkeypatch, cursor=None, raise_on_connect=False) -> _FakePyodbc:
    fake = _FakePyodbc(cursor=cursor, raise_on_connect=raise_on_connect)
    monkeypatch.setitem(sys.modules, "pyodbc", fake)
    return fake


def test_read_table_maps_columns_to_csv_identical_keys(monkeypatch):
    cursor = _FakeCursor(
        description=[("client_id",), ("display_name",), ("esg_preference",)],
        rows=[("cli-001", "Northbridge Family Trust", True)],
    )
    _install_pyodbc(monkeypatch, cursor=cursor)

    rows = fabric_data.read_table("clients")

    # Boolean normalises to "True"/"False" exactly as the CSV provider yields.
    assert rows == [
        {"client_id": "cli-001", "display_name": "Northbridge Family Trust", "esg_preference": "True"}
    ]
    assert "SELECT * FROM dbo.clients" in cursor.executed[0][0]


def test_query_normalizes_numeric_and_null(monkeypatch):
    from decimal import Decimal

    cursor = _FakeCursor(
        description=[("weight",), ("aum_musd",), ("rationale",)],
        rows=[(0.0887, Decimal("42.5"), None)],
    )
    _install_pyodbc(monkeypatch, cursor=cursor)

    rows = fabric_data.query("SELECT weight, aum_musd, rationale FROM dbo.holdings")

    assert rows == [{"weight": "0.0887", "aum_musd": "42.5", "rationale": None}]


def test_connection_failure_raises_fabric_data_error_with_remediation(monkeypatch):
    _install_pyodbc(monkeypatch, raise_on_connect=True)

    with pytest.raises(fabric_data.FabricDataError) as exc:
        fabric_data.read_table("clients")

    assert "ODBC Driver 18" in str(exc.value)


def test_invalid_identifier_rejected(monkeypatch):
    _install_pyodbc(monkeypatch, cursor=_FakeCursor([], []))

    with pytest.raises(fabric_data.FabricDataError):
        fabric_data.read_table("clients; DROP TABLE clients")


def test_access_token_passed_and_never_logged(monkeypatch, caplog):
    cursor = _FakeCursor(description=[("period",)], rows=[("Q3-2025",)])
    fake = _install_pyodbc(monkeypatch, cursor=cursor)

    with caplog.at_level(logging.DEBUG, logger="app.services.fabric_data"):
        fabric_data.read_table("portfolio_performance")

    # The AAD token struct is supplied via the ODBC access-token attribute (1256)...
    attrs = fake.connect_calls[0]["attrs_before"]
    assert fabric_data._SQL_COPT_SS_ACCESS_TOKEN in attrs
    # ...and the raw token is never emitted to logs.
    assert "SUPER-SECRET-ACCESS-TOKEN" not in caplog.text


def test_read_periods_orders_chronologically(monkeypatch):
    # Warehouse returns them already ordered by (year, quarter); provider preserves order.
    cursor = _FakeCursor(
        description=[("period",)],
        rows=[("Q3-2025",), ("Q4-2025",), ("Q1-2026",), ("Q2-2026",)],
    )
    _install_pyodbc(monkeypatch, cursor=cursor)

    assert fabric_data.read_periods() == ["Q3-2025", "Q4-2025", "Q1-2026", "Q2-2026"]
