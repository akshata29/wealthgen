"""Scan for market events and show which mandates would get an event brief.

The on-demand form of an autonomous market watcher: detects the period's market
events (curated bulletins with affected tickers) and cross-references them
against every mandate's real holdings. Prints the affected portfolios and the
exact command/URL to generate an event-driven brief for each.

Run:
    cd backend
    python -m scripts.scan_events --period Q1-2026
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.services import market_events


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--period", default="Q1-2026", help="Reporting period, e.g. Q1-2026.")
    args = parser.parse_args()

    results = market_events.scan(args.period)
    if not results:
        print(f"No market events with portfolio impact found for {args.period}.")
        return

    for item in results:
        ev = item["event"]
        print(f"\nEVENT: {ev['title']}  [{ev['channel']} · {ev['publisher']}]")
        print(f"  Affected funds: {', '.join(ev['affected_tickers'])}")
        if ev.get("advisor_talking_point"):
            print(f"  Talking point: {ev['advisor_talking_point']}")
        print("  Affected client portfolios:")
        for m in item["affected_mandates"]:
            holds = ", ".join(
                f"{h['ticker']} {h['weight'] * 100:.1f}%" for h in m["affected_holdings"]
            )
            print(f"    - {m['display_name']} ({m['mandate_id']}): {holds}")
            print(
                f"      -> generate: POST /api/commentary/generate "
                f"{{mandate_id:'{m['mandate_id']}', period:'{args.period}', "
                f"commentary_type:'event_driven'}}"
            )


if __name__ == "__main__":
    main()
