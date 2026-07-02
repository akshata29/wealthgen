"""Reference data service — reads the synthetic advisory dataset from disk.

Loads `data/synthetic/catalog.json` and the `fabric_iq/*.csv` fact tables produced
by `scripts.synthetic.generate`, and exposes typed query helpers that back the
/clients, /mandates, /performance, and /events endpoints.

The dataset is a local demo corpus (no secrets, demo-safe display names). In a
production build these reads would target Fabric IQ / OneLake instead; the query
surface here is intentionally the same shape so that swap is mechanical.
"""

from __future__ import annotations

import csv
import json
import logging
from functools import lru_cache
from pathlib import Path

from app.models.portfolio import (
    AttributionSegment,
    Client,
    ClientSummary,
    Holding,
    IndexReturn,
    Mandate,
    NextBestAction,
    PerformanceReport,
    PerformanceSummary,
    PositioningChange,
    SectorComparison,
    VixEvent,
)

logger = logging.getLogger(__name__)

# backend/app/services/reference_data.py -> parents[2] == backend/
_DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "synthetic"
_FABRIC = _DATA_ROOT / "fabric_iq"


class DatasetNotFoundError(RuntimeError):
    """Raised when the synthetic dataset has not been generated yet."""


def _require(path: Path) -> Path:
    if not path.exists():
        raise DatasetNotFoundError(
            f"{path} not found. Run 'python -m scripts.synthetic.generate' first."
        )
    return path


def _read_csv(name: str) -> list[dict]:
    with _require(_FABRIC / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _f(value: str | None) -> float:
    return float(value) if value not in (None, "") else 0.0


# --------------------------------------------------------------------------- #
# Catalog (clients + mandates + periods)
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def _catalog() -> dict:
    with _require(_DATA_ROOT / "catalog.json").open(encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def _benchmark_names() -> dict[str, str]:
    names: dict[str, str] = {}
    for row in _read_csv("benchmarks.csv"):
        names[row["benchmark_id"]] = row["name"]
    return names


def _to_mandate(raw: dict) -> Mandate:
    return Mandate(
        mandate_id=raw["mandate_id"],
        display_name=raw["display_name"],
        client_id=raw["client_id"],
        strategy=raw["strategy"],
        benchmark_id=raw["benchmark_id"],
        benchmark_name=_benchmark_names().get(raw["benchmark_id"]),
        base_currency=raw["base_currency"],
        inception=raw["inception"],
        aum_musd=float(raw["aum_musd"]),
    )


def list_periods() -> list[str]:
    return [p["period"] for p in _catalog()["periods"]]


def latest_period() -> str:
    return list_periods()[-1]


def list_mandates(client_id: str | None = None) -> list[Mandate]:
    mandates = [_to_mandate(m) for m in _catalog()["mandates"]]
    if client_id:
        mandates = [m for m in mandates if m.client_id == client_id]
    return mandates


def get_mandate(mandate_id: str) -> Mandate | None:
    for m in _catalog()["mandates"]:
        if m["mandate_id"] == mandate_id:
            return _to_mandate(m)
    return None


def list_clients() -> list[ClientSummary]:
    summaries: list[ClientSummary] = []
    for raw in _catalog()["clients"]:
        client = Client.model_validate(raw)
        mandates = list_mandates(client.client_id)
        summaries.append(
            ClientSummary(
                **client.model_dump(),
                mandates=mandates,
                total_aum_musd=round(sum(m.aum_musd for m in mandates), 1),
            )
        )
    return summaries


def get_client(client_id: str) -> ClientSummary | None:
    return next((c for c in list_clients() if c.client_id == client_id), None)


# --------------------------------------------------------------------------- #
# Fact tables
# --------------------------------------------------------------------------- #
def get_performance(mandate_id: str, period: str) -> PerformanceSummary | None:
    for row in _read_csv("portfolio_performance.csv"):
        if row["mandate_id"] == mandate_id and row["period"] == period:
            return PerformanceSummary(
                mandate_id=mandate_id,
                period=period,
                total_return_net_pct=_f(row["total_return_net_pct"]),
                benchmark_return_pct=_f(row["benchmark_return_pct"]),
                active_return_bps=_f(row["active_return_bps"]),
                tracking_error_pct=_f(row["tracking_error_pct"]),
                information_ratio=_f(row["information_ratio"]),
                ex_ante_vol_pct=_f(row["ex_ante_vol_pct"]),
                sharpe=_f(row["sharpe"]),
                max_drawdown_pct=_f(row["max_drawdown_pct"]),
            )
    return None


def get_holdings(mandate_id: str, period: str) -> list[Holding]:
    return [
        Holding(
            mandate_id=mandate_id,
            period=period,
            ticker=row["ticker"],
            instrument=row["instrument"],
            isin=row["isin"],
            asset_class=row["asset_class"],
            sector=row["sector"],
            region=row["region"],
            weight=_f(row["weight"]),
            market_value_usd=_f(row["market_value_usd"]),
            period_return_pct=_f(row["period_return_pct"]),
        )
        for row in _read_csv("holdings.csv")
        if row["mandate_id"] == mandate_id and row["period"] == period
    ]


def get_attribution(mandate_id: str, period: str) -> list[AttributionSegment]:
    return [
        AttributionSegment(
            segment=row["segment"],
            portfolio_weight=_f(row["portfolio_weight"]),
            benchmark_weight=_f(row["benchmark_weight"]),
            portfolio_return=_f(row["portfolio_return"]),
            benchmark_return=_f(row["benchmark_return"]),
            allocation_bps=_f(row["allocation_bps"]),
            selection_bps=_f(row["selection_bps"]),
            interaction_bps=_f(row["interaction_bps"]),
            source_id=row["source_id"],
        )
        for row in _read_csv("attribution.csv")
        if row["mandate_id"] == mandate_id and row["period"] == period
    ]


def get_positioning(mandate_id: str, period: str) -> list[PositioningChange]:
    return [
        PositioningChange(
            mandate_id=mandate_id,
            period=period,
            description=row["description"],
            direction=row["direction"],
            magnitude=row["magnitude"] or None,
            rationale=row["rationale"] or None,
            source_id=row["source_id"],
        )
        for row in _read_csv("positioning_changes.csv")
        if row["mandate_id"] == mandate_id and row["period"] == period
    ]


def get_index_returns(period: str) -> list[IndexReturn]:
    return [
        IndexReturn(
            index_name=row["index_name"],
            period_return_pct=_f(row["period_return_pct"]),
            source_id=row["source_id"],
        )
        for row in _read_csv("market_index_returns.csv")
        if row["period"] == period
    ]


def get_fx_moves(period: str) -> list[tuple[str, float, str]]:
    """Return (pair, change_pct, source_id) tuples for the period."""
    return [
        (row["pair"], _f(row["change_pct"]), row["source_id"])
        for row in _read_csv("fx_moves.csv")
        if row["period"] == period
    ]


def get_vix_events(only_triggers: bool = False) -> list[VixEvent]:
    events = [
        VixEvent(
            period=row["period"],
            vix_close=_f(row["vix_close"]),
            event_trigger=row["event_trigger"].lower() == "true",
            regime=row["regime"],
            headline=row["headline"],
        )
        for row in _read_csv("vix_events.csv")
    ]
    return [e for e in events if e.event_trigger] if only_triggers else events


def get_vix_event(period: str) -> VixEvent | None:
    return next((e for e in get_vix_events() if e.period == period), None)


# --------------------------------------------------------------------------- #
# Composed reports
# --------------------------------------------------------------------------- #
def _to_sector_comparison(seg: AttributionSegment) -> SectorComparison:
    return SectorComparison(
        segment=seg.segment,
        portfolio_weight=seg.portfolio_weight,
        benchmark_weight=seg.benchmark_weight,
        portfolio_return=seg.portfolio_return,
        benchmark_return=seg.benchmark_return,
        total_effect_bps=round(seg.total_effect_bps, 1),
        source_id=seg.source_id,
    )


def build_performance_report(mandate_id: str, period: str) -> PerformanceReport | None:
    mandate = get_mandate(mandate_id)
    summary = get_performance(mandate_id, period)
    if mandate is None or summary is None:
        return None

    segments = get_attribution(mandate_id, period)
    ranked = sorted(segments, key=lambda s: s.total_effect_bps, reverse=True)
    contributors = [_to_sector_comparison(s) for s in ranked[:3] if s.total_effect_bps > 0]
    detractors = [_to_sector_comparison(s) for s in reversed(ranked[-3:]) if s.total_effect_bps < 0]

    return PerformanceReport(
        mandate=mandate,
        period=period,
        summary=summary,
        benchmark_name=mandate.benchmark_name or mandate.benchmark_id,
        top_contributors=contributors,
        top_detractors=detractors,
        index_returns=get_index_returns(period),
        positioning_changes=get_positioning(mandate_id, period),
    )


# --------------------------------------------------------------------------- #
# Next-best-action derivation (mirrors work_iq/next_best_action_playbook.md)
# --------------------------------------------------------------------------- #
_LIFE_EVENT_ACTIONS: dict[str, tuple[str, str]] = {
    "Approaching retirement (5y)": (
        "Review the glide-path toward income",
        "Consider gradually de-risking toward income-generating assets as the horizon shortens.",
    ),
    "Liquidity event (business sale)": (
        "Stage deployment of new liquidity",
        "Phase cash into the mandate to manage timing risk; review available tax wrappers.",
    ),
    "New child / education planning": (
        "Introduce a goals-based education sleeve",
        "Add an education sub-portfolio with an age-based glide-path.",
    ),
    "Intergenerational wealth transfer": (
        "Review estate structure and beneficiary mandates",
        "Align the mandate with succession goals and beneficiary suitability.",
    ),
}


def next_best_actions(mandate_id: str, period: str | None = None) -> list[NextBestAction]:
    mandate = get_mandate(mandate_id)
    if mandate is None:
        return []
    period = period or latest_period()
    client = get_client(mandate.client_id)
    actions: list[NextBestAction] = []

    if client and client.life_event and client.life_event in _LIFE_EVENT_ACTIONS:
        title, rationale = _LIFE_EVENT_ACTIONS[client.life_event]
        actions.append(
            NextBestAction(
                title=title,
                rationale=rationale,
                risk_warning="Capital at risk; suitability review required before acting.",
                trigger_type="life_event",
                source=f"Client life event: {client.life_event}",
            )
        )

    event = get_vix_event(period)
    if event and event.event_trigger:
        actions.append(
            NextBestAction(
                title="Reassure with the plan amid elevated volatility",
                rationale=(
                    f"VIX closed at {event.vix_close:.0f} ({event.regime}). Lead with the plan and the "
                    "portfolio's existing ballast; consider rebalancing into weakness where suitable."
                ),
                risk_warning="Past performance is not a reliable indicator of future results.",
                trigger_type="market_event",
                source=f"Market event ({period}): {event.headline}",
            )
        )
    return actions
