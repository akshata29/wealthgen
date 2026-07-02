"""Generate realistic, deterministic synthetic datasets for the three IQ sources.

Run:
    cd backend
    python -m scripts.synthetic.generate            # writes ./data/synthetic/**
    python -m scripts.synthetic.generate --out C:/tmp/wg

Output tree:
    data/synthetic/
      fabric_iq/     advisors.csv, clients.csv, mandates.csv, benchmarks.csv,
                     holdings.csv, portfolio_performance.csv, attribution.csv,
                     positioning_changes.csv, market_index_returns.csv,
                     fx_moves.csv, vix_events.csv
      foundry_iq/    facts.jsonl (all fact-sheet SourceFacts for the search index)
                     factsheets/<mandate>_<period>.md (human-readable sheets)
      work_iq/       house_view.md, brand_voice_style_guide.md,
                     disclosures_UK.md, disclosures_US.md, tone_playbook.md,
                     next_best_action_playbook.md
      catalog.json   machine-readable clients + mandates (unblocks the UI list)

Design guarantees:
  * Deterministic — same inputs produce byte-identical output (seeded RNG).
  * Reconciled — Brinson-Fachler effects sum exactly to the active return.
  * Model-aligned — records mirror app.models.* field names/shapes.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import random
from dataclasses import asdict
from pathlib import Path

from scripts.synthetic import reference as ref
from scripts.synthetic.reference import (
    BENCHMARKS_BY_ID,
    CLIENTS_BY_ID,
    INSTRUMENTS_BY_TICKER,
    MarketScenario,
    Mandate,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Global seed so the entire dataset is reproducible.
MASTER_SEED = 20260702


def _rng(*parts: str | int) -> random.Random:
    """Deterministic RNG keyed by the given parts."""
    return random.Random(f"{MASTER_SEED}:" + ":".join(str(p) for p in parts))


# --------------------------------------------------------------------------- #
# Per-instrument returns and portfolio weights
# --------------------------------------------------------------------------- #
# Base period return (%) per sector under each regime; idiosyncratic noise added.
_SECTOR_BASE_RETURN: dict[str, dict[str, float]] = {
    "risk-on": {
        "Information Technology": 9.5, "Financials": 4.0, "Consumer Staples": 1.5,
        "Health Care": 3.0, "Energy": 2.0, "Utilities": 1.0, "Real Estate": 3.5,
        "Commodities": 2.5, "Government": 0.6, "Credit": 1.4, "Cash": 1.0,
    },
    "rotation": {
        "Information Technology": -1.5, "Financials": 5.5, "Consumer Staples": 3.0,
        "Health Care": 4.0, "Energy": 4.5, "Utilities": 2.5, "Real Estate": 2.0,
        "Commodities": 3.5, "Government": -0.4, "Credit": 0.9, "Cash": 1.0,
    },
    "risk-off": {
        "Information Technology": -12.0, "Financials": -8.0, "Consumer Staples": -1.0,
        "Health Care": -3.0, "Energy": -6.0, "Utilities": 1.5, "Real Estate": -7.0,
        "Commodities": 4.0, "Government": 3.2, "Credit": 1.1, "Cash": 1.0,
    },
}


def _instrument_weights(mandate: Mandate) -> dict[str, float]:
    """Seeded portfolio weights (fractions summing to 1.0) for a mandate."""
    rng = _rng("weights", mandate.mandate_id)
    raw: dict[str, float] = {}
    for ticker in mandate.target_holdings:
        inst = INSTRUMENTS_BY_TICKER[ticker]
        # Anchor by asset class to keep portfolios plausible.
        anchor = {
            "Equity": 8.0, "Fixed Income": 6.0, "Alternatives": 3.0, "Cash": 2.0,
        }[inst.asset_class]
        raw[ticker] = max(0.5, anchor + rng.uniform(-2.5, 3.5))
    total = sum(raw.values())
    return {t: round(w / total, 4) for t, w in raw.items()}


def _instrument_return(ticker: str, scenario: MarketScenario) -> float:
    """Seeded instrument period return (%) given the market regime."""
    inst = INSTRUMENTS_BY_TICKER[ticker]
    base = _SECTOR_BASE_RETURN[scenario.regime][inst.sector]
    rng = _rng("ret", ticker, scenario.period)
    idio = rng.uniform(-2.0, 2.5)
    return round(base + idio, 2)


# --------------------------------------------------------------------------- #
# Fabric IQ — holdings, performance, attribution, positioning
# --------------------------------------------------------------------------- #
def _holdings_rows(mandate: Mandate, scenario: MarketScenario) -> list[dict]:
    weights = _instrument_weights(mandate)
    rows: list[dict] = []
    for ticker, weight in weights.items():
        inst = INSTRUMENTS_BY_TICKER[ticker]
        rows.append(
            {
                "mandate_id": mandate.mandate_id,
                "period": scenario.period,
                "ticker": ticker,
                "instrument": inst.name,
                "isin": inst.isin,
                "asset_class": inst.asset_class,
                "sector": inst.sector,
                "region": inst.region,
                "weight": weight,
                "market_value_usd": round(mandate.aum_musd * 1e6 * weight, 2),
                "period_return_pct": _instrument_return(ticker, scenario),
            }
        )
    return rows


def _benchmark_sector_return(sector: str, scenario: MarketScenario) -> float:
    """Benchmark's sector return (%) — market base with a small seeded delta."""
    base = _SECTOR_BASE_RETURN[scenario.regime][sector]
    rng = _rng("bmret", sector, scenario.period)
    return round(base + rng.uniform(-0.8, 0.8), 2)


def _attribution_rows(mandate: Mandate, scenario: MarketScenario) -> tuple[list[dict], dict]:
    """Brinson-Fachler attribution by sector; effects sum to active return.

    Returns (attribution_rows, performance_summary).
    """
    holdings = _holdings_rows(mandate, scenario)
    benchmark = BENCHMARKS_BY_ID[mandate.benchmark_id]

    # Portfolio sector weights and returns.
    port_w: dict[str, float] = {}
    port_r_num: dict[str, float] = {}
    for h in holdings:
        sec = h["sector"]
        w = h["weight"]
        port_w[sec] = port_w.get(sec, 0.0) + w
        port_r_num[sec] = port_r_num.get(sec, 0.0) + w * (h["period_return_pct"] / 100.0)
    port_r = {s: (port_r_num[s] / port_w[s] if port_w[s] else 0.0) for s in port_w}

    # Benchmark sector weights (fractions) and returns (fractions).
    bench_w = dict(benchmark.sector_weights)
    bench_r = {s: _benchmark_sector_return(s, scenario) / 100.0 for s in bench_w}

    # Benchmark total return (fraction).
    rb_total = sum(bench_w[s] * bench_r.get(s, 0.0) for s in bench_w)

    sectors = sorted(set(port_w) | set(bench_w))
    rows: list[dict] = []
    port_total = 0.0
    for sec in sectors:
        wp = port_w.get(sec, 0.0)
        wb = bench_w.get(sec, 0.0)
        rp = port_r.get(sec, bench_r.get(sec, 0.0))
        rb = bench_r.get(sec, 0.0)
        port_total += wp * rp

        allocation = (wp - wb) * (rb - rb_total)
        selection = wb * (rp - rb)
        interaction = (wp - wb) * (rp - rb)
        rows.append(
            {
                "mandate_id": mandate.mandate_id,
                "period": scenario.period,
                "segment": sec,
                "portfolio_weight": round(wp, 4),
                "benchmark_weight": round(wb, 4),
                "portfolio_return": round(rp, 4),
                "benchmark_return": round(rb, 4),
                "allocation_bps": round(allocation * 10000, 1),
                "selection_bps": round(selection * 10000, 1),
                "interaction_bps": round(interaction * 10000, 1),
                "source_id": f"attr:{sec.lower().replace(' ', '_')}",
            }
        )

    active = port_total - rb_total
    tracking_error = round(_rng("te", mandate.mandate_id, scenario.period).uniform(1.4, 4.2), 2)
    ex_ante_vol = round(
        {
            "conservative": 5.5, "balanced": 8.5, "growth": 12.0, "aggressive": 15.5,
        }[CLIENTS_BY_ID[mandate.client_id].risk_profile.value]
        + _rng("vol", mandate.mandate_id, scenario.period).uniform(-1.0, 1.0),
        2,
    )
    perf = {
        "mandate_id": mandate.mandate_id,
        "period": scenario.period,
        "total_return_net_pct": round(port_total * 100, 2),
        "benchmark_return_pct": round(rb_total * 100, 2),
        "active_return_bps": round(active * 10000, 1),
        "tracking_error_pct": tracking_error,
        "information_ratio": round((active * 10000) / (tracking_error * 100) if tracking_error else 0.0, 2),
        "ex_ante_vol_pct": ex_ante_vol,
        "sharpe": round(
            (port_total * 100 - 4.0) / ex_ante_vol if ex_ante_vol else 0.0, 2
        ),
        "max_drawdown_pct": round(
            -abs(scenario.equity_return) * _rng("dd", mandate.mandate_id, scenario.period).uniform(0.4, 0.9), 2
        ),
    }
    return rows, perf


_POSITIONING_TEMPLATES = [
    ("Trimmed Information Technology into strength", "trim", "-150 bps", "Lock in gains after outsized AI-led rally; manage concentration risk."),
    ("Added to Health Care on defensive quality", "add", "+120 bps", "Rotate toward earnings resilience amid growth-scare."),
    ("Initiated Utilities for downside ballast", "initiate", "+80 bps", "Increase low-beta exposure ahead of expected volatility."),
    ("Extended duration in Government bonds", "duration", "+0.4y", "Position for a lower forward rate path."),
    ("Reduced Energy on demand concerns", "trim", "-60 bps", "Fade cyclical exposure as leading indicators soften."),
    ("Exited a low-conviction Real Estate sleeve", "exit", "-90 bps", "Recycle capital into higher-conviction ideas."),
]


def _positioning_rows(mandate: Mandate, scenario: MarketScenario) -> list[dict]:
    rng = _rng("pos", mandate.mandate_id, scenario.period)
    count = rng.randint(2, 3)
    chosen = rng.sample(_POSITIONING_TEMPLATES, count)
    rows: list[dict] = []
    for i, (desc, direction, magnitude, rationale) in enumerate(chosen):
        rows.append(
            {
                "mandate_id": mandate.mandate_id,
                "period": scenario.period,
                "description": desc,
                "direction": direction,
                "magnitude": magnitude,
                "rationale": rationale,
                "source_id": f"pos:{scenario.period.lower()}:{i}",
            }
        )
    return rows


# --------------------------------------------------------------------------- #
# Fabric IQ — market context (index returns, FX, VIX events)
# --------------------------------------------------------------------------- #
def _market_index_rows(scenario: MarketScenario) -> list[dict]:
    rng = _rng("idx", scenario.period)
    indices = [
        ("Developed market equities", scenario.equity_return),
        ("Emerging market equities", round(scenario.equity_return + rng.uniform(-3, 3), 1)),
        ("Global aggregate bonds", scenario.bond_return),
        ("Global high yield", round(scenario.bond_return + rng.uniform(-1.5, 2.5), 1)),
        ("Gold", round(rng.uniform(-2, 6), 1)),
        ("Brent crude", round(rng.uniform(-8, 8), 1)),
    ]
    return [
        {
            "period": scenario.period,
            "index_name": name,
            "period_return_pct": val,
            "source_id": f"lseg:idx:{name.lower().replace(' ', '_')}:{scenario.period.lower()}",
        }
        for name, val in indices
    ]


def _fx_rows(scenario: MarketScenario) -> list[dict]:
    rng = _rng("fx", scenario.period)
    pairs = ["GBP/USD", "EUR/USD", "USD/JPY"]
    return [
        {
            "period": scenario.period,
            "pair": p,
            "change_pct": round(rng.uniform(-3.5, 3.5), 2),
            "source_id": f"lseg:fx:{p.replace('/', '').lower()}:{scenario.period.lower()}",
        }
        for p in pairs
    ]


def _vix_row(scenario: MarketScenario) -> dict:
    return {
        "period": scenario.period,
        "vix_close": scenario.vix_close,
        "event_trigger": scenario.vix_trigger,
        "regime": scenario.regime,
        "headline": scenario.narrative_headline,
    }


# --------------------------------------------------------------------------- #
# Foundry IQ — fund fact-sheet SourceFacts (for the PDF search index)
# --------------------------------------------------------------------------- #
def _factsheet_facts(mandate: Mandate, scenario: MarketScenario, perf: dict) -> list[dict]:
    """SourceFacts mirroring what Content Understanding would extract from a PDF."""
    rng = _rng("sheet", mandate.mandate_id, scenario.period)
    weights = _instrument_weights(mandate)
    top = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)[:5]
    m = mandate.mandate_id
    p = scenario.period

    facts: list[dict] = [
        _fact(f"cu:{m}:{p}:total_return", "Total return (net)", f"{perf['total_return_net_pct']:+.2f}%", "%"),
        _fact(f"cu:{m}:{p}:benchmark_return", "Benchmark return", f"{perf['benchmark_return_pct']:+.2f}%", "%"),
        _fact(f"cu:{m}:{p}:active_return", "Active return", f"{perf['active_return_bps']:+.0f} bps", "bps"),
        _fact(f"cu:{m}:{p}:tracking_error", "Tracking error", f"{perf['tracking_error_pct']:.2f}%", "%"),
        _fact(f"cu:{m}:{p}:vol", "Ex-ante volatility", f"{perf['ex_ante_vol_pct']:.2f}%", "%"),
        _fact(f"cu:{m}:{p}:sharpe", "Sharpe ratio", f"{perf['sharpe']:.2f}", None),
        _fact(f"cu:{m}:{p}:max_drawdown", "Maximum drawdown", f"{perf['max_drawdown_pct']:.2f}%", "%"),
        _fact(f"cu:{m}:{p}:ocf", "Ongoing charges (OCF)", f"{rng.uniform(0.35, 0.85):.2f}%", "%"),
        _fact(f"cu:{m}:{p}:yield", "Distribution yield", f"{rng.uniform(1.8, 3.6):.2f}%", "%"),
        _fact(f"cu:{m}:{p}:duration", "Fixed income duration", f"{rng.uniform(4.5, 7.5):.1f}y", "years"),
    ]
    for i, (ticker, w) in enumerate(top):
        inst = INSTRUMENTS_BY_TICKER[ticker]
        facts.append(
            _fact(
                f"cu:{m}:{p}:top{i + 1}",
                f"Top holding #{i + 1}: {inst.name}",
                f"{w * 100:.1f}%",
                "%",
            )
        )
    # Attach mandate_id so the search index filter works.
    for f in facts:
        f["mandate_id"] = m
        f["period"] = p
    return facts


def _fact(source_id: str, label: str, value: str, unit: str | None) -> dict:
    return {
        "source_id": source_id,
        "origin": "content_understanding",
        "label": label,
        "value": value,
        "unit": unit,
        "confidence": 0.97,
        "region": None,
    }


def _factsheet_markdown(mandate: Mandate, scenario: MarketScenario, perf: dict, facts: list[dict]) -> str:
    client = CLIENTS_BY_ID[mandate.client_id]
    benchmark = BENCHMARKS_BY_ID[mandate.benchmark_id]
    lines = [
        f"# Fund Fact Sheet — {mandate.display_name}",
        "",
        f"- **Mandate ID:** {mandate.mandate_id}",
        f"- **Reporting period:** {scenario.label}",
        f"- **Strategy:** {mandate.strategy}",
        f"- **Benchmark:** {benchmark.name}",
        f"- **Base currency:** {mandate.base_currency}",
        f"- **AUM:** {mandate.aum_musd:.1f}m {mandate.base_currency}",
        f"- **Risk profile:** {client.risk_profile.value.title()}",
        "",
        "## Performance",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Total return (net) | {perf['total_return_net_pct']:+.2f}% |",
        f"| Benchmark return | {perf['benchmark_return_pct']:+.2f}% |",
        f"| Active return | {perf['active_return_bps']:+.0f} bps |",
        f"| Tracking error | {perf['tracking_error_pct']:.2f}% |",
        f"| Information ratio | {perf['information_ratio']:.2f} |",
        f"| Sharpe ratio | {perf['sharpe']:.2f} |",
        f"| Max drawdown | {perf['max_drawdown_pct']:.2f}% |",
        "",
        "## Fund facts",
        "",
    ]
    for f in facts:
        if f["source_id"].split(":")[-1] in {"ocf", "yield", "duration"}:
            lines.append(f"- {f['label']}: {f['value']}")
    lines += ["", "## Market context", "", f"> {scenario.narrative_headline}", ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Work IQ — house content documents
# --------------------------------------------------------------------------- #
def _work_iq_docs() -> dict[str, str]:
    house_view = """# House View — Investment Office

_Last updated: Q2 2026. Owner: Global Investment Committee._

## Strategic stance

- **Overall:** Modestly pro-risk. We favour quality equities and are neutral duration.
- **Equities:** Prefer developed-market quality and selective AI beneficiaries; trim
  after outsized rallies to manage concentration.
- **Fixed income:** Neutral duration with a bias to extend on rate-path repricing;
  favour investment-grade credit over high yield.
- **Alternatives:** Retain gold as a portfolio diversifier and tail hedge.
- **Cash:** Keep tactical dry powder for volatility-driven opportunities.

## Key risks we are watching

1. Growth-scare episodes that spike the VIX above 30.
2. Sticky services inflation delaying the rate-cut path.
3. Narrow equity leadership and crowding in mega-cap technology.

## What this means for client commentary

- Emphasise diversification and the role of each asset class in the mandate's goals.
- When markets fall, lead with the plan and the ballast already in the portfolio.
- Never imply guaranteed outcomes; frame the outlook as a base case with risks.
"""

    brand_voice = """# Brand-Voice Style Guide

## Principles

- **Clear over clever.** Short sentences. One idea per sentence.
- **Grounded.** Every number ties to a source; never invent figures.
- **Balanced.** Pair any positive with the associated risk.
- **Respectful of the reader.** Match complexity to the client's financial literacy.

## Voice by audience

| Audience | Voice | Jargon | Length |
| --- | --- | --- | --- |
| Client | Warm, reassuring, plain English | Avoid; define if unavoidable | Concise |
| Institutional | Precise, evidence-led | Expected | Fuller detail |
| Investment Committee | Terse, decision-oriented | Expected | Bulleted |

## Banned phrasing

- "Guaranteed", "risk-free", "can't lose", "sure thing".
- Absolute predictions ("will rise", "will outperform"). Use "we expect" / "our base case".
- Unsourced superlatives ("best-in-class") without evidence.

## Preferred constructions

- "Over the quarter, the portfolio returned +X.X%, ahead of / behind its benchmark by Y bps."
- "This reflects [driver], partly offset by [detractor]."
- "Looking ahead, our base case is …, though [risk] could change the picture."
"""

    disclosures_uk = """# Approved Language & Disclosures — UK

_Jurisdiction: UK. Regime: FCA. Review owner: Compliance._

## Mandatory disclaimers (client communications)

- Capital at risk. The value of investments and any income from them can fall as
  well as rise and you may get back less than you invested.
- Past performance is not a reliable indicator of future results.
- This communication is for information only and is not personal advice or a
  recommendation to buy or sell any investment.
- Where performance is shown net of fees, ongoing charges apply as set out in the
  fund documentation.

## Approved phrasings

- "Capital at risk" (never "low risk" without qualification).
- "Our base case" / "we expect" (never "will").

## Prohibited

- Any implication of guaranteed returns or capital protection.
- Tax statements without "depends on individual circumstances and may change".
"""

    disclosures_us = """# Approved Language & Disclosures — US

_Jurisdiction: US. Regime: SEC / FINRA. Review owner: Compliance._

## Mandatory disclaimers (client communications)

- Investing involves risk, including the possible loss of principal.
- Past performance does not guarantee future results.
- This material is for informational purposes only and does not constitute
  investment advice or an offer or solicitation.
- Diversification does not ensure a profit or protect against loss.

## Approved phrasings

- "May", "we believe", "our current view" (avoid promissory language).

## Prohibited

- Performance claims without required time periods and net-of-fee context.
- Testimonials or predictions of specific returns.
"""

    tone_playbook = """# Tone & Ease Playbook

Maps the client's **risk profile**, **financial literacy**, and **tone preference**
to concrete narrative controls. The narrative generator reads these dials.

## Financial literacy -> language

| Literacy | Sentence length | Jargon | Analogies |
| --- | --- | --- | --- |
| Novice | Very short | None (define everything) | Everyday analogies encouraged |
| Informed | Short | Light, defined on first use | Occasional |
| Expert | Standard | Expected | Rare |

## Risk profile -> emphasis

| Risk profile | Lead with | Reassurance level |
| --- | --- | --- |
| Conservative | Capital preservation, income, ballast | High |
| Balanced | Diversification and progress to goals | Medium |
| Growth | Long-term compounding, drivers of return | Medium |
| Aggressive | Conviction ideas and opportunity set | Lower |

## Tone preference -> register

| Tone | Register |
| --- | --- |
| Warm | Personable, second-person, encouraging |
| Neutral | Even, factual |
| Formal | Reserved, third-person, precise |

## Non-financial-language mode

When enabled (typically Novice + Warm), replace: "drawdown" -> "temporary dip",
"volatility" -> "ups and downs", "attribution" -> "what helped and what held us back",
"duration" -> "sensitivity to interest-rate changes".
"""

    nba_playbook = """# Next-Best-Action Playbook

Life-event and market-event triggers mapped to compliant, suitability-aware
recommendations. Always framed as "consider", never as instruction, and always
gated by human approval before client delivery.

## Life-event triggers

| Trigger | Suggested next best action |
| --- | --- |
| Approaching retirement (5y) | Review glide-path; consider de-risking toward income. |
| Liquidity event (business sale) | Stage cash deployment; discuss tax wrappers. |
| New child / education planning | Introduce goals-based education sub-portfolio. |
| Intergenerational wealth transfer | Review estate structure and beneficiary mandates. |

## Market-event triggers

| Trigger | Suggested next best action |
| --- | --- |
| VIX spike > 30 | Reassure with plan; highlight ballast; consider rebalancing into weakness. |
| Sharp equity drawdown | Reaffirm long-term plan; avoid forced selling; review cash needs. |
| Rate-path repricing | Review duration positioning; discuss reinvestment of maturities. |

## Guardrails

- Every recommendation includes rationale, risk warning, and source attribution.
- No specific security recommendation without a suitability check.
- All actions require PM + Compliance approval (amber human-in-the-loop gate).
"""

    return {
        "house_view.md": house_view,
        "brand_voice_style_guide.md": brand_voice,
        "disclosures_UK.md": disclosures_uk,
        "disclosures_US.md": disclosures_us,
        "tone_playbook.md": tone_playbook,
        "next_best_action_playbook.md": nba_playbook,
    }


# --------------------------------------------------------------------------- #
# Writers
# --------------------------------------------------------------------------- #
def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    logger.info("  wrote %-42s (%d rows)", path.name, len(rows))


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    logger.info("  wrote %s", path.name)


def generate(out_root: Path) -> None:
    fabric = out_root / "fabric_iq"
    foundry = out_root / "foundry_iq"
    sheets = foundry / "factsheets"
    work = out_root / "work_iq"

    # --- Reference dimensions ---
    _write_csv(fabric / "advisors.csv", [asdict(a) for a in ref.ADVISORS])
    _write_csv(
        fabric / "clients.csv",
        [
            {
                **{k: (v.value if isinstance(v, ref.Enum) else v) for k, v in asdict(c).items()},
            }
            for c in ref.CLIENTS
        ],
    )
    _write_csv(fabric / "mandates.csv", [
        {**asdict(m), "target_holdings": "|".join(m.target_holdings)} for m in ref.MANDATES
    ])
    _write_csv(
        fabric / "benchmarks.csv",
        [
            {"benchmark_id": b.benchmark_id, "name": b.name, "sector": sec, "weight": w}
            for b in ref.BENCHMARKS
            for sec, w in b.sector_weights.items()
        ],
    )

    # --- Fact tables + fact sheets across mandates x periods ---
    holdings_all: list[dict] = []
    perf_all: list[dict] = []
    attribution_all: list[dict] = []
    positioning_all: list[dict] = []
    facts_all: list[dict] = []

    for mandate in ref.MANDATES:
        for scenario in ref.PERIODS:
            holdings_all.extend(_holdings_rows(mandate, scenario))
            attribution_rows, perf = _attribution_rows(mandate, scenario)
            attribution_all.extend(attribution_rows)
            perf_all.append(perf)
            positioning_all.extend(_positioning_rows(mandate, scenario))

            facts = _factsheet_facts(mandate, scenario, perf)
            facts_all.extend(facts)
            _write_text(
                sheets / f"{mandate.mandate_id}_{scenario.period}.md",
                _factsheet_markdown(mandate, scenario, perf, facts),
            )

    _write_csv(fabric / "holdings.csv", holdings_all)
    _write_csv(fabric / "portfolio_performance.csv", perf_all)
    _write_csv(fabric / "attribution.csv", attribution_all)
    _write_csv(fabric / "positioning_changes.csv", positioning_all)

    # --- Market context ---
    idx_rows = [r for s in ref.PERIODS for r in _market_index_rows(s)]
    fx_rows = [r for s in ref.PERIODS for r in _fx_rows(s)]
    vix_rows = [_vix_row(s) for s in ref.PERIODS]
    _write_csv(fabric / "market_index_returns.csv", idx_rows)
    _write_csv(fabric / "fx_moves.csv", fx_rows)
    _write_csv(fabric / "vix_events.csv", vix_rows)

    # --- Foundry IQ facts (JSONL for the search index) ---
    foundry.mkdir(parents=True, exist_ok=True)
    facts_path = foundry / "facts.jsonl"
    with facts_path.open("w", encoding="utf-8") as fh:
        for fact in facts_all:
            fh.write(json.dumps(fact) + "\n")
    logger.info("  wrote %-42s (%d facts)", facts_path.name, len(facts_all))

    # --- Work IQ documents ---
    for name, text in _work_iq_docs().items():
        _write_text(work / name, text)

    # --- Machine-readable catalog (unblocks the UI client/portfolio list) ---
    catalog = {
        "advisors": [asdict(a) for a in ref.ADVISORS],
        "clients": [
            {k: (v.value if isinstance(v, ref.Enum) else v) for k, v in asdict(c).items()}
            for c in ref.CLIENTS
        ],
        "mandates": [asdict(m) for m in ref.MANDATES],
        "periods": [asdict(s) for s in ref.PERIODS],
    }
    _write_text(out_root / "catalog.json", json.dumps(catalog, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate WealthGen synthetic datasets.")
    parser.add_argument(
        "--out",
        default=str(Path(__file__).resolve().parents[2] / "data" / "synthetic"),
        help="Output directory (default: backend/data/synthetic).",
    )
    args = parser.parse_args()
    out_root = Path(args.out)

    logger.info("Generating synthetic datasets -> %s", out_root)
    logger.info("Fabric IQ:")
    generate(out_root)
    logger.info("Done. Next: load facts into the search index (see scripts/load_synthetic_facts.py).")


if __name__ == "__main__":
    main()
