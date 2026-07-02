"""Deterministic reference catalog — the seed universe for synthetic generation.

Everything downstream (holdings, attribution, fact sheets, briefs) is derived
from these hand-authored, realistic entities so the demo is coherent: the same
clients, mandates, benchmarks, and instruments appear consistently across the
Fabric IQ / Foundry IQ / Work IQ datasets.

No randomness lives here — this is the fixed spine. `generate.py` layers seeded
per-period variation on top.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RiskProfile(str, Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    GROWTH = "growth"
    AGGRESSIVE = "aggressive"


class FinancialLiteracy(str, Enum):
    """Drives the 'ease' / non-financial-language dial in the narrative."""

    NOVICE = "novice"
    INFORMED = "informed"
    EXPERT = "expert"


class TonePreference(str, Enum):
    WARM = "warm"
    NEUTRAL = "neutral"
    FORMAL = "formal"


@dataclass(frozen=True)
class Advisor:
    advisor_id: str
    name: str
    team: str
    jurisdiction: str


@dataclass(frozen=True)
class Client:
    client_id: str
    display_name: str  # never a real full name in logs; demo-safe
    advisor_id: str
    jurisdiction: str
    risk_profile: RiskProfile
    financial_literacy: FinancialLiteracy
    tone_preference: TonePreference
    segment: str  # e.g. 'Private Client', 'Family Office', 'Institutional'
    life_event: str | None  # drives next-best-action recommendations
    esg_preference: bool


@dataclass(frozen=True)
class Instrument:
    ticker: str
    name: str
    isin: str
    asset_class: str  # 'Equity' | 'Fixed Income' | 'Alternatives' | 'Cash'
    sector: str  # GICS sector or FI segment
    region: str


@dataclass(frozen=True)
class Benchmark:
    benchmark_id: str
    name: str
    # sector -> benchmark weight (fractions, sum ~ 1.0)
    sector_weights: dict[str, float]


@dataclass(frozen=True)
class Mandate:
    mandate_id: str
    display_name: str
    client_id: str
    strategy: str
    benchmark_id: str
    base_currency: str
    inception: str
    aum_musd: float  # AUM in millions USD (demo scale, no real client data)
    target_holdings: list[str]  # instrument tickers in the strategy universe


# --------------------------------------------------------------------------- #
# Advisors
# --------------------------------------------------------------------------- #
ADVISORS: list[Advisor] = [
    Advisor("adv-001", "A. Okafor", "UK Private Wealth", "UK"),
    Advisor("adv-002", "M. Lindqvist", "US Private Wealth", "US"),
    Advisor("adv-003", "R. Nakamura", "Global Family Office", "UK"),
]


# --------------------------------------------------------------------------- #
# Instrument universe (realistic identifiers, GICS sectors)
# --------------------------------------------------------------------------- #
INSTRUMENTS: list[Instrument] = [
    Instrument("MSFT", "Microsoft Corp", "US5949181045", "Equity", "Information Technology", "US"),
    Instrument("NVDA", "NVIDIA Corp", "US67066G1040", "Equity", "Information Technology", "US"),
    Instrument("AAPL", "Apple Inc", "US0378331005", "Equity", "Information Technology", "US"),
    Instrument("JPM", "JPMorgan Chase", "US46625H1005", "Equity", "Financials", "US"),
    Instrument("HSBA", "HSBC Holdings", "GB0005405286", "Equity", "Financials", "UK"),
    Instrument("NESN", "Nestle SA", "CH0038863350", "Equity", "Consumer Staples", "Europe"),
    Instrument("ASML", "ASML Holding", "NL0010273215", "Equity", "Information Technology", "Europe"),
    Instrument("UNH", "UnitedHealth Group", "US91324P1021", "Equity", "Health Care", "US"),
    Instrument("XOM", "Exxon Mobil", "US30231G1022", "Equity", "Energy", "US"),
    Instrument("NEE", "NextEra Energy", "US65339F1012", "Equity", "Utilities", "US"),
    Instrument("IEF", "iShares 7-10 Year Treasury Bond ETF", "US4642874402", "Fixed Income", "Government", "US"),
    Instrument("LQD", "iShares iBoxx $ IG Corporate Bond ETF", "US4642872265", "Fixed Income", "Credit", "US"),
    Instrument("IGLT", "iShares Core UK Gilts UCITS ETF", "IE00B1FZSB30", "Fixed Income", "Government", "UK"),
    Instrument("GLD", "SPDR Gold Shares", "US78463V1070", "Alternatives", "Commodities", "Global"),
    Instrument("VNQ", "Vanguard Real Estate ETF", "US9229085538", "Alternatives", "Real Estate", "US"),
    Instrument("BIL", "SPDR Bloomberg 1-3 Month T-Bill ETF", "US78468R6633", "Cash", "Cash", "US"),
]


# --------------------------------------------------------------------------- #
# Benchmarks (sector weights are illustrative and sum to ~1.0)
# --------------------------------------------------------------------------- #
BENCHMARKS: list[Benchmark] = [
    Benchmark(
        "BM-GBL-6040",
        "60/40 Global Balanced (MSCI ACWI / Bloomberg Global Agg)",
        {
            "Information Technology": 0.16,
            "Financials": 0.09,
            "Consumer Staples": 0.04,
            "Health Care": 0.07,
            "Energy": 0.03,
            "Utilities": 0.02,
            "Real Estate": 0.02,
            "Commodities": 0.03,
            "Government": 0.30,
            "Credit": 0.19,
            "Cash": 0.05,
        },
    ),
    Benchmark(
        "BM-GBL-EQ",
        "MSCI ACWI (Global Equity)",
        {
            "Information Technology": 0.26,
            "Financials": 0.16,
            "Consumer Staples": 0.07,
            "Health Care": 0.11,
            "Energy": 0.05,
            "Utilities": 0.03,
            "Real Estate": 0.03,
            "Commodities": 0.04,
            "Government": 0.12,
            "Credit": 0.09,
            "Cash": 0.04,
        },
    ),
    Benchmark(
        "BM-US-CONS",
        "US Conservative (30/70 S&P 500 / US Agg)",
        {
            "Information Technology": 0.10,
            "Financials": 0.06,
            "Consumer Staples": 0.03,
            "Health Care": 0.05,
            "Energy": 0.02,
            "Utilities": 0.02,
            "Real Estate": 0.01,
            "Commodities": 0.01,
            "Government": 0.42,
            "Credit": 0.23,
            "Cash": 0.05,
        },
    ),
]


# --------------------------------------------------------------------------- #
# Clients (demo-safe display names; no real PII)
# --------------------------------------------------------------------------- #
CLIENTS: list[Client] = [
    Client(
        "cli-001", "Northbridge Family Trust", "adv-001", "UK",
        RiskProfile.BALANCED, FinancialLiteracy.INFORMED, TonePreference.WARM,
        "Private Client", "Approaching retirement (5y)", esg_preference=True,
    ),
    Client(
        "cli-002", "Halvorsen Holdings", "adv-002", "US",
        RiskProfile.GROWTH, FinancialLiteracy.EXPERT, TonePreference.FORMAL,
        "Family Office", None, esg_preference=False,
    ),
    Client(
        "cli-003", "Meadowlark Endowment", "adv-003", "UK",
        RiskProfile.CONSERVATIVE, FinancialLiteracy.EXPERT, TonePreference.FORMAL,
        "Institutional", None, esg_preference=True,
    ),
    Client(
        "cli-004", "Rivera Private Wealth", "adv-002", "US",
        RiskProfile.AGGRESSIVE, FinancialLiteracy.INFORMED, TonePreference.NEUTRAL,
        "Private Client", "Liquidity event (business sale)", esg_preference=False,
    ),
    Client(
        "cli-005", "Ashcombe Pension Scheme", "adv-001", "UK",
        RiskProfile.CONSERVATIVE, FinancialLiteracy.EXPERT, TonePreference.FORMAL,
        "Institutional", None, esg_preference=True,
    ),
    Client(
        "cli-006", "Thornton Household", "adv-001", "UK",
        RiskProfile.BALANCED, FinancialLiteracy.NOVICE, TonePreference.WARM,
        "Private Client", "New child / education planning", esg_preference=True,
    ),
    Client(
        "cli-007", "Delacroix Family Office", "adv-003", "US",
        RiskProfile.GROWTH, FinancialLiteracy.INFORMED, TonePreference.NEUTRAL,
        "Family Office", "Intergenerational wealth transfer", esg_preference=False,
    ),
    Client(
        "cli-008", "Sable Ridge Foundation", "adv-003", "US",
        RiskProfile.BALANCED, FinancialLiteracy.EXPERT, TonePreference.FORMAL,
        "Institutional", None, esg_preference=True,
    ),
]


# --------------------------------------------------------------------------- #
# Mandates (portfolios) — one or more per client
# --------------------------------------------------------------------------- #
_CORE_BALANCED = [
    "MSFT", "NVDA", "AAPL", "JPM", "HSBA", "NESN", "ASML", "UNH",
    "XOM", "NEE", "IEF", "LQD", "IGLT", "GLD", "VNQ", "BIL",
]
_GROWTH_TILT = ["MSFT", "NVDA", "AAPL", "ASML", "UNH", "JPM", "VNQ", "LQD", "BIL"]
_CONSERVATIVE = ["IEF", "LQD", "IGLT", "NESN", "UNH", "NEE", "GLD", "BIL"]

MANDATES: list[Mandate] = [
    Mandate(
        "northbridge-global-balanced", "Northbridge Global Balanced", "cli-001",
        "Global multi-asset balanced with ESG screen", "BM-GBL-6040", "GBP",
        "2019-03-01", 42.5, _CORE_BALANCED,
    ),
    Mandate(
        "halvorsen-global-growth", "Halvorsen Global Growth", "cli-002",
        "Global equity growth with thematic tilt", "BM-GBL-EQ", "USD",
        "2017-06-15", 128.0, _GROWTH_TILT,
    ),
    Mandate(
        "meadowlark-core-income", "Meadowlark Core Income", "cli-003",
        "Capital-preservation income mandate", "BM-US-CONS", "GBP",
        "2015-01-10", 310.0, _CONSERVATIVE,
    ),
    Mandate(
        "rivera-opportunistic-equity", "Rivera Opportunistic Equity", "cli-004",
        "High-conviction global equity", "BM-GBL-EQ", "USD",
        "2021-09-01", 26.0, _GROWTH_TILT,
    ),
    Mandate(
        "ashcombe-ldi-core", "Ashcombe LDI Core", "cli-005",
        "Liability-driven conservative income", "BM-US-CONS", "GBP",
        "2014-04-01", 540.0, _CONSERVATIVE,
    ),
    Mandate(
        "thornton-lifestyle-balanced", "Thornton Lifestyle Balanced", "cli-006",
        "Goals-based balanced with education glide-path", "BM-GBL-6040", "GBP",
        "2020-11-01", 3.8, _CORE_BALANCED,
    ),
    Mandate(
        "delacroix-global-growth", "Delacroix Global Growth", "cli-007",
        "Multi-generational growth", "BM-GBL-EQ", "USD",
        "2016-02-01", 96.0, _GROWTH_TILT,
    ),
    Mandate(
        "sableridge-balanced-esg", "Sable Ridge Balanced ESG", "cli-008",
        "Mission-aligned balanced (Article 8)", "BM-GBL-6040", "USD",
        "2018-07-01", 205.0, _CORE_BALANCED,
    ),
]


# --------------------------------------------------------------------------- #
# Reporting periods + market regime scenarios (drive event-driven briefs)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class MarketScenario:
    """A period-level market regime; drives index returns, VIX, and event briefs."""

    period: str
    label: str
    regime: str  # 'risk-on' | 'risk-off' | 'rotation'
    vix_close: float
    vix_trigger: bool  # True => a VIX-spike event brief is warranted
    equity_return: float  # broad equity index period return (%)
    bond_return: float
    narrative_headline: str


PERIODS: list[MarketScenario] = [
    MarketScenario(
        "Q3-2025", "Q3 2025", "risk-on", 14.2, False, 5.8, 1.1,
        "Soft-landing optimism and AI capex broaden the equity rally.",
    ),
    MarketScenario(
        "Q4-2025", "Q4 2025", "rotation", 18.6, False, 2.3, -0.4,
        "Leadership rotates from mega-cap tech toward value and small caps.",
    ),
    MarketScenario(
        "Q1-2026", "Q1 2026", "risk-off", 31.4, True, -6.9, 2.7,
        "A VIX spike above 30 on growth-scare and rate-path repricing.",
    ),
    MarketScenario(
        "Q2-2026", "Q2 2026", "risk-on", 15.9, False, 4.6, 0.6,
        "Markets recover as disinflation resumes and earnings beat.",
    ),
]


# --------------------------------------------------------------------------- #
# Convenience lookups
# --------------------------------------------------------------------------- #
INSTRUMENTS_BY_TICKER: dict[str, Instrument] = {i.ticker: i for i in INSTRUMENTS}
BENCHMARKS_BY_ID: dict[str, Benchmark] = {b.benchmark_id: b for b in BENCHMARKS}
CLIENTS_BY_ID: dict[str, Client] = {c.client_id: c for c in CLIENTS}
MANDATES_BY_ID: dict[str, Mandate] = {m.mandate_id: m for m in MANDATES}
ADVISORS_BY_ID: dict[str, Advisor] = {a.advisor_id: a for a in ADVISORS}


def sectors() -> list[str]:
    """Stable ordered list of sectors used across benchmarks/holdings."""
    seen: list[str] = []
    for bm in BENCHMARKS:
        for sec in bm.sector_weights:
            if sec not in seen:
                seen.append(sec)
    return seen
