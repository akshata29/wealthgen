"""Provider parity — csv and fabric modes yield identical typed reference data.

The fabric provider is stubbed to return the same synthetic rows as the local CSVs
(as real Fabric normalisation would: all values as strings, booleans as
"True"/"False"), so reference_data must produce byte-identical typed results in
either DATA_SOURCE_MODE.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from app.services import fabric_data, reference_data

_FABRIC_CSV = Path(reference_data.__file__).resolve().parents[2] / "data" / "synthetic" / "fabric_iq"
_MANDATE = "northbridge-global-balanced"
_PERIOD = "Q3-2025"


class _FakeSettings:
    def __init__(self, mode: str):
        self.data_source_mode = mode
        self.fabric_sql_schema = "dbo"
        self.fabric_sql_endpoint = "wh.datawarehouse.fabric.microsoft.com"
        self.fabric_database = "wealthgen-wh"


def _csv_rows(name: str) -> list[dict]:
    # Mirror the load->DB->provider round-trip: empty CSV cells become SQL NULL,
    # which fabric_data.query returns as None.
    with (_FABRIC_CSV / f"{name}.csv").open(encoding="utf-8") as fh:
        return [
            {col: (val if val != "" else None) for col, val in row.items()}
            for row in csv.DictReader(fh)
        ]


def _stub_fabric(monkeypatch) -> None:
    """Make the fabric provider echo the CSV rows (mirrors real normalisation)."""
    monkeypatch.setattr(fabric_data, "read_table", _csv_rows)
    monkeypatch.setattr(fabric_data, "read_clients", lambda: _csv_rows("clients"))
    monkeypatch.setattr(fabric_data, "read_mandates", lambda: _csv_rows("mandates"))
    monkeypatch.setattr(fabric_data, "read_advisors", lambda: _csv_rows("advisors"))

    def _periods() -> list[str]:
        seen: list[str] = []
        for row in _csv_rows("portfolio_performance"):
            if row["period"] not in seen:
                seen.append(row["period"])
        return sorted(seen, key=lambda p: (p[3:], p[:2]))

    monkeypatch.setattr(fabric_data, "read_periods", _periods)


def _collect(monkeypatch, mode: str) -> dict:
    monkeypatch.setattr(reference_data, "get_settings", lambda: _FakeSettings(mode))
    reference_data._benchmark_names.cache_clear()
    reference_data._catalog.cache_clear()
    if mode == "fabric":
        _stub_fabric(monkeypatch)
    return {
        "periods": reference_data.list_periods(),
        "clients": [c.model_dump() for c in reference_data.list_clients()],
        "holdings": [h.model_dump() for h in reference_data.get_holdings(_MANDATE, _PERIOD)],
        "performance": reference_data.get_performance(_MANDATE, _PERIOD).model_dump(),
        "mandates": [m.model_dump() for m in reference_data.list_mandates()],
    }


def test_csv_and_fabric_providers_are_identical(monkeypatch):
    with monkeypatch.context() as m:
        csv_result = _collect(m, "csv")
    with monkeypatch.context() as m:
        fabric_result = _collect(m, "fabric")

    assert set(csv_result["periods"]) == set(fabric_result["periods"])
    assert csv_result["periods"] == fabric_result["periods"]
    assert csv_result["clients"] == fabric_result["clients"]
    assert csv_result["holdings"] == fabric_result["holdings"]
    assert csv_result["performance"] == fabric_result["performance"]
    assert csv_result["mandates"] == fabric_result["mandates"]


@pytest.mark.parametrize("mode", ["csv", "fabric"])
def test_each_provider_returns_non_empty(monkeypatch, mode):
    with monkeypatch.context() as m:
        result = _collect(m, mode)
    assert result["periods"]
    assert result["clients"]
    assert result["holdings"]
