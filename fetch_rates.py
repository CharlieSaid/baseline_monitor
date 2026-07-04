#!/usr/bin/env python3
"""
fetch_rates.py — fetches current savings rates and writes data/rates.json.

Sources live in scrapers/ (one module per provider).

Run daily via GitHub Actions. Writes rates.json and appends one daily
snapshot to history.json (at most once per calendar day).
Exits with status 1 if any source fails or returns no data (so CI can alert).
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from scrapers import SOURCES

OUTPUT = Path(__file__).parent / "data" / "rates.json"
HISTORY = Path(__file__).parent / "data" / "history.json"

RATE_SOURCES = [
    {
        "key": source.__name__.rsplit(".", 1)[-1],
        "name": source.NAME,
        "fetch": source.fetch_rate,
        "url": source.URL,
    }
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


def load_history() -> list:
    if not HISTORY.exists():
        return []
    return json.loads(HISTORY.read_text())


def record_history(rates_by_key: dict[str, float], today: str, *, force: bool = False) -> None:
    """Append today's rates to history.json, at most once per calendar day."""
    history = load_history()
    last_date = history[-1]["date"] if history else None

    if last_date == today and not force:
        print(f"History already recorded for {today}, skipping.")
        return

    entry = {"date": today, "rates": rates_by_key}
    if last_date == today and force:
        history[-1] = entry
        action = "Updated"
    else:
        history.append(entry)
        action = "Appended"

    HISTORY.write_text(json.dumps(history, indent=2) + "\n")
    print(f"{action} {HISTORY} ({HISTORY.stat().st_size} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch savings rates and update data files.")
    parser.add_argument(
        "--force-history",
        action="store_true",
        help="Replace today's history entry instead of skipping (for local testing).",
    )
    args = parser.parse_args()

    today = date.today().isoformat()
    results = []
    rates_by_key: dict[str, float] = {}
    errors = []

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    for source in RATE_SOURCES:
        name = source["name"]
        try:
            rate = require_rate(source["fetch"](), name)
            results.append({"name": name, "rate": rate, "url": source["url"]})
            rates_by_key[source["key"]] = rate
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

    record_history(rates_by_key, today, force=args.force_history)


if __name__ == "__main__":
    main()
