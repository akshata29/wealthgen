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
# Instrument universe — REAL iShares ETF building blocks (one per sleeve).
#
# Portfolios are constructed from these publicly-traded funds; the `sector`
# field carries the fund *sleeve* (US Large Cap Equity, US Treasuries, ...), so
# Brinson-Fachler attribution runs per-fund. Real fact sheets for these funds
# live in data/real_funds/pdfs (see scripts/download_real_factsheets.py).
# --------------------------------------------------------------------------- #
INSTRUMENTS: list[Instrument] = [
    Instrument("IVV", "iShares Core S&P 500 ETF", "US4642872000", "Equity", "US Large Cap Equity", "US"),
    Instrument("IJR", "iShares Core S&P Small-Cap ETF", "US4642878049", "Equity", "US Small Cap Equity", "US"),
    Instrument("IEFA", "iShares Core MSCI EAFE ETF", "US46432F3391", "Equity", "International Developed Equity", "Global ex-US"),
    Instrument("IEMG", "iShares Core MSCI Emerging Markets ETF", "US46434G1031", "Equity", "Emerging Market Equity", "Emerging Markets"),
    Instrument("ESGU", "iShares ESG Aware MSCI USA ETF", "US46435G4128", "Equity", "US Equity ESG", "US"),
    Instrument("IXC", "iShares Global Energy ETF", "US4642871689", "Equity", "Global Energy Equity", "Global"),
    Instrument("AGG", "iShares Core U.S. Aggregate Bond ETF", "US4642872265", "Fixed Income", "US Aggregate Bonds", "US"),
    Instrument("LQD", "iShares iBoxx $ IG Corporate Bond ETF", "US4642872273", "Fixed Income", "Investment Grade Credit", "US"),
    Instrument("IEF", "iShares 7-10 Year Treasury Bond ETF", "US4642874402", "Fixed Income", "US Treasuries", "US"),
    Instrument("IAU", "iShares Gold Trust", "US4642851053", "Alternatives", "Gold", "Global"),
]


# --------------------------------------------------------------------------- #
# Benchmarks — model-portfolio sleeve weights (fund sleeves, sum ~1.0)
# --------------------------------------------------------------------------- #
BENCHMARKS: list[Benchmark] = [
    Benchmark(
        "BM-GBL-6040",
        "60/40 Global Balanced (MSCI ACWI / Bloomberg Global Agg)",
        {
            "US Large Cap Equity": 0.28,
            "International Developed Equity": 0.12,
            "Emerging Market Equity": 0.06,
            "US Small Cap Equity": 0.05,
            "Global Energy Equity": 0.04,
            "US Aggregate Bonds": 0.18,
            "Investment Grade Credit": 0.12,
            "US Treasuries": 0.10,
            "Gold": 0.05,
        },
    ),
    Benchmark(
        "BM-GBL-EQ",
        "MSCI ACWI (Global Equity)",
        {
            "US Large Cap Equity": 0.45,
            "International Developed Equity": 0.22,
            "Emerging Market Equity": 0.13,
            "US Small Cap Equity": 0.10,
            "Global Energy Equity": 0.07,
            "Gold": 0.03,
        },
    ),
    Benchmark(
        "BM-US-CONS",
        "US Conservative (30/70 S&P 500 / US Agg)",
        {
            "US Large Cap Equity": 0.18,
            "International Developed Equity": 0.06,
            "Emerging Market Equity": 0.02,
            "US Aggregate Bonds": 0.34,
            "Investment Grade Credit": 0.20,
            "US Treasuries": 0.15,
            "Gold": 0.05,
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
# Mandates (portfolios) — one or more per client, built from real ETF sleeves
# --------------------------------------------------------------------------- #
_CORE_BALANCED = ["IVV", "IEFA", "IEMG", "IJR", "IXC", "AGG", "LQD", "IEF", "IAU"]
_GROWTH_TILT = ["IVV", "IEFA", "IEMG", "IJR", "IXC", "LQD", "IAU"]
_CONSERVATIVE = ["IVV", "IEFA", "AGG", "LQD", "IEF", "IAU"]
_ESG_BALANCED = ["ESGU", "IEFA", "IEMG", "IXC", "AGG", "LQD", "IEF", "IAU"]

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
        "2018-07-01", 205.0, _ESG_BALANCED,
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
