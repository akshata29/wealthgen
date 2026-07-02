"""Approved-language / disclosure selection by jurisdiction.

Disclaimers are SELECTED from a versioned, pre-cleared library (never free-written).
In production the library is sourced from Work IQ; the built-in defaults below are
the fallback set of approved wordings so the gate is always compliant-by-construction.
"""

from __future__ import annotations

# Versioned, pre-approved disclosure wordings keyed by jurisdiction.
DISCLOSURE_LIBRARY: dict[str, list[str]] = {
    "UK": [
        "Past performance is not a reliable indicator of future results.",
        "Any forward-looking statements reflect the firm's house view and are not a "
        "reliable indicator of future performance; outcomes may be better or worse.",
        "The value of investments and any income from them can fall as well as rise and "
        "is not guaranteed.",
    ],
    "US": [
        "Performance is presented net of fees. Past performance does not guarantee future results.",
        "This communication is for informational purposes and does not predict or project "
        "future performance.",
    ],
}


def select_disclaimers(jurisdictions: list[str]) -> list[str]:
    """Return the ordered, de-duplicated set of approved disclaimers for the given jurisdictions."""
    selected: list[str] = []
    for jurisdiction in jurisdictions:
        for text in DISCLOSURE_LIBRARY.get(jurisdiction.upper(), []):
            if text not in selected:
                selected.append(text)
    return selected
