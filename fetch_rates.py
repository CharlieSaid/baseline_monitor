#!/usr/bin/env python3
"""
fetch_rates.py — fetches current savings rates and writes data/rates.json.

Sources live in scrapers/ (one module per provider).

Run daily via GitHub Actions. Writes a ~200-byte JSON file.
Exits with status 1 if any source fails or returns no data (so CI can alert).
"""

import json
import sys
from datetime import date
from pathlib import Path

from scrapers import SOURCES

OUTPUT = Path(__file__).parent / "data" / "rates.json"

RATE_SOURCES = [
    {"name": source.NAME, "fetch": source.fetch_rate, "url": source.URL}
    for source in SOURCES
]


def require_rate(rate: float | None, source_name: str) -> float:
    """Reject empty or invalid fetch results so failures are never silent."""
    if rate is None:
        raise ValueError(f"{source_name}: fetch returned no data")
    if not isinstance(rate, (int, float)):
        raise ValueError(f"{source_name}: fetch returned non-numeric data: {rate!r}")
    if rate <= 0:
        raise ValueError(f"{source_name}: fetch returned invalid rate ({rate}%)")
    return round(float(rate), 2)


def alert(message: str) -> None:
    print(f"ALERT: {message}", file=sys.stderr)


def main() -> None:
    today = date.today().isoformat()
    results = []
    errors = []

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    for source in RATE_SOURCES:
        name = source["name"]
        try:
            rate = require_rate(source["fetch"](), name)
            results.append({"name": name, "rate": rate, "url": source["url"]})
            print(f"  ✓ {name}: {rate}%")
        except Exception as exc:
            message = f"{name}: {exc}"
            errors.append(message)
            alert(message)
            print(f"  ✗ {name}: {exc}", file=sys.stderr)

    if not results:
        alert("All rate sources failed — not overwriting existing data.")
        sys.exit(1)

    results.sort(key=lambda r: r["rate"], reverse=True)

    payload = {"updated": today, "rates": results}
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"\nWrote {OUTPUT} ({OUTPUT.stat().st_size} bytes)")

    if errors:
        alert(
            f"{len(errors)}/{len(RATE_SOURCES)} rate sources failed; "
            "rates.json may be incomplete."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
