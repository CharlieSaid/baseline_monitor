#!/usr/bin/env python3
"""
validate_rates.py — sanity-check rates.json (and recent history) after a scrape.

Exits 0 if data looks plausible, 1 if anomalies are found (so CI can open an issue).

Checks:
  1. rates.json exists and is well-formed
  2. Every registered scraper key is present
  3. Absolute bounds for HYSAs (benchmarks excluded)
  4. Day-over-day change vs prior history (1.5pp HYSAs, 1.0pp benchmarks)
  5. Median outlier for HYSAs only (benchmarks excluded — they often sit lower)
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

from scrapers import SOURCES

ROOT = Path(__file__).parent
RATES_PATH = ROOT / "data" / "rates.json"
HISTORY_PATH = ROOT / "data" / "history.json"

# Percentage points (APY units), not relative percent.
MIN_RATE = 0.5
MAX_RATE = 12.0
MAX_DAY_CHANGE = 1.5
MAX_BENCHMARK_DAY_CHANGE = 1.0
MAX_MEDIAN_DEVIATION = 1.5

BENCHMARK_KEYS = frozenset({"tbill_4week", "vmfxx"})

EXPECTED_KEYS = {source.__name__.rsplit(".", 1)[-1] for source in SOURCES}
NAME_BY_KEY = {
    source.__name__.rsplit(".", 1)[-1]: source.NAME for source in SOURCES
}


def alert(message: str) -> None:
    print(f"ALERT: {message}", file=sys.stderr)


def load_rates() -> dict:
    if not RATES_PATH.exists():
        raise ValueError(f"Missing {RATES_PATH}")
    data = json.loads(RATES_PATH.read_text())
    if not isinstance(data.get("rates"), list) or not data["rates"]:
        raise ValueError("rates.json has no rates array")
    return data


def load_history() -> list:
    if not HISTORY_PATH.exists():
        return []
    return json.loads(HISTORY_PATH.read_text())


def check_completeness(rates: list[dict]) -> list[str]:
    issues = []
    keys = {r.get("key") for r in rates}
    missing = sorted(EXPECTED_KEYS - keys)
    extra = sorted(keys - EXPECTED_KEYS - {None})
    if missing:
        issues.append(f"Missing {len(missing)} source(s): {', '.join(missing)}")
    if extra:
        issues.append(f"Unexpected key(s): {', '.join(extra)}")
    if len(rates) != len(EXPECTED_KEYS):
        issues.append(
            f"Expected {len(EXPECTED_KEYS)} rates, found {len(rates)}"
        )
    return issues


def check_bounds(rates: list[dict]) -> list[str]:
    """Absolute bounds for HYSAs only — benchmarks are checked day-over-day."""
    issues = []
    for r in rates:
        key = r.get("key")
        if key in BENCHMARK_KEYS:
            continue
        rate = r["rate"]
        name = r.get("name") or key
        if not isinstance(rate, (int, float)):
            issues.append(f"{name}: non-numeric rate {rate!r}")
            continue
        if rate < MIN_RATE or rate > MAX_RATE:
            issues.append(
                f"{name}: {rate}% outside plausible bounds "
                f"[{MIN_RATE}%, {MAX_RATE}%]"
            )
    return issues


def day_over_day_issues(payload: dict, history: list) -> list[str]:
    """Flag sources whose rate jumped beyond their day-change threshold."""
    if not history:
        return []

    today = payload.get("updated")
    prior = None
    for entry in reversed(history):
        if entry["date"] != today:
            prior = entry
            break
    if prior is None:
        return []

    issues = []
    today_by_key = {r["key"]: r for r in payload["rates"] if "key" in r}
    for key, item in today_by_key.items():
        if key not in prior["rates"]:
            continue
        prev = prior["rates"][key]
        curr = item["rate"]
        delta = abs(curr - prev)
        limit = (
            MAX_BENCHMARK_DAY_CHANGE
            if key in BENCHMARK_KEYS
            else MAX_DAY_CHANGE
        )
        if delta > limit:
            name = item.get("name") or NAME_BY_KEY.get(key, key)
            issues.append(
                f"{name}: day-over-day change {prev}% → {curr}% "
                f"(Δ {delta:.2f}pp > {limit}pp) vs {prior['date']}"
            )
    return issues


def median_outlier_issues(rates: list[dict]) -> list[str]:
    """Flag HYSA rates more than MAX_MEDIAN_DEVIATION pp from the HYSA median."""
    hysa = [
        r
        for r in rates
        if r.get("key") not in BENCHMARK_KEYS
        and isinstance(r.get("rate"), (int, float))
    ]
    if len(hysa) < 3:
        return []

    median = statistics.median(r["rate"] for r in hysa)
    issues = []
    for r in hysa:
        rate = r["rate"]
        deviation = abs(rate - median)
        if deviation > MAX_MEDIAN_DEVIATION:
            name = r.get("name") or r.get("key")
            issues.append(
                f"{name}: {rate}% is {deviation:.2f}pp from HYSA median "
                f"{median:.2f}% (threshold {MAX_MEDIAN_DEVIATION}pp)"
            )
    return issues


def main() -> None:
    try:
        payload = load_rates()
    except Exception as exc:
        alert(str(exc))
        sys.exit(1)

    rates = payload["rates"]
    history = load_history()

    issues: list[str] = []
    issues.extend(check_completeness(rates))
    issues.extend(check_bounds(rates))
    issues.extend(day_over_day_issues(payload, history))
    issues.extend(median_outlier_issues(rates))

    if issues:
        alert(f"{len(issues)} data anomal{'y' if len(issues) == 1 else 'ies'} detected:")
        for issue in issues:
            alert(f"  • {issue}")
        sys.exit(1)

    print(
        f"Validation OK — {len(rates)} rates, "
        f"HYSA bounds [{MIN_RATE}%, {MAX_RATE}%], "
        f"HYSA day-change {MAX_DAY_CHANGE}pp, "
        f"benchmark day-change {MAX_BENCHMARK_DAY_CHANGE}pp, "
        f"HYSA median deviation {MAX_MEDIAN_DEVIATION}pp"
    )


if __name__ == "__main__":
    main()
