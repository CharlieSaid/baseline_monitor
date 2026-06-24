#!/usr/bin/env python3
"""
fetch_rates.py — scrapes current savings rates and writes data/rates.json.

Sources:
  - T-Bill (4-week): Treasury FRB H.15 data release (JSON)
  - VMFXX:           Vanguard fund detail page
  - HYSAs:           Each bank's public rate page

Run daily via GitHub Actions. Writes a ~200-byte JSON file.
"""

import json
import re
import sys
from datetime import date, timezone, datetime
from pathlib import Path
import urllib.request
import urllib.error

OUTPUT = Path(__file__).parent / "data" / "rates.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fetch(url: str, timeout: int = 10) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "rate-leaderboard/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def find_first_percent(html: str, pattern: str) -> float | None:
    """Return the first float that follows `pattern` in `html`, or None."""
    m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
    if m:
        try:
            return round(float(m.group(1)), 2)
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Individual fetchers — each returns a float (APY/rate %) or raises
# ---------------------------------------------------------------------------

def fetch_tbill_4week() -> float:
    """4-week T-Bill secondary-market yield from the Fed H.15 JSON release."""
    url = "https://www.federalreserve.gov/releases/h15/current/h15.json"
    raw = fetch(url)
    data = json.loads(raw)

    # Navigate: data["H15"] > series where name contains "4-WEEK" and "TREASURY BILLS"
    for series in data.get("H15", {}).get("series", []):
        desc = series.get("description", "").upper()
        if "4-WEEK" in desc and "TREASURY" in desc and "COUPON" not in desc:
            # Observations are [{date, value}, ...]; grab the last non-ND value
            for obs in reversed(series.get("observations", [])):
                v = obs.get("value", "ND")
                if v != "ND":
                    return round(float(v), 2)

    raise ValueError("4-week T-Bill rate not found in H15 feed")


def fetch_vmfxx() -> float:
    """VMFXX 7-day SEC yield from Vanguard's public fund detail page."""
    url = "https://investor.vanguard.com/investment-products/money-markets/profile/vmfxx#overview"
    html = fetch(url)
    # Vanguard renders "X.XX%" for the 7-day SEC yield
    rate = find_first_percent(html, r"7-day\s+SEC\s+yield[^%]{0,80}?([\d]+\.[\d]+)\s*%")
    if rate is not None:
        return rate

    # Fallback: look for any "X.XX%" near "SEC yield" text
    rate = find_first_percent(html, r"SEC\s+yield[^%]{0,120}?([\d]+\.[\d]+)")
    if rate is not None:
        return rate

    raise ValueError("VMFXX rate not found on Vanguard page")


def fetch_sofi_hysa() -> float:
    url = "https://www.sofi.com/banking/savings-account/"
    html = fetch(url)
    rate = find_first_percent(html, r"([\d]+\.[\d]+)\s*%\s*APY")
    if rate is not None:
        return rate
    raise ValueError("SoFi HYSA rate not found")


def fetch_marcus_hysa() -> float:
    url = "https://www.marcus.com/us/en/savings/high-yield-savings"
    html = fetch(url)
    rate = find_first_percent(html, r"([\d]+\.[\d]+)\s*%\s*APY")
    if rate is not None:
        return rate
    raise ValueError("Marcus HYSA rate not found")


# ---------------------------------------------------------------------------
# Rate definitions — add or remove entries here to change the leaderboard
# ---------------------------------------------------------------------------

RATE_SOURCES = [
    {
        "name": "T-Bill (4-week)",
        "fetch": fetch_tbill_4week,
        "url": "https://www.treasurydirect.gov/auctions/upcoming/",
    },
    {
        "name": "VMFXX",
        "fetch": fetch_vmfxx,
        "url": "https://investor.vanguard.com/investment-products/money-markets/profile/vmfxx#overview",
    },
    {
        "name": "SoFi HYSA",
        "fetch": fetch_sofi_hysa,
        "url": "https://www.sofi.com/banking/savings-account/",
    },
    {
        "name": "Marcus HYSA",
        "fetch": fetch_marcus_hysa,
        "url": "https://www.marcus.com/us/en/savings/high-yield-savings",
    },
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    today = date.today().isoformat()
    results = []
    errors = []

    for source in RATE_SOURCES:
        try:
            rate = source["fetch"]()
            results.append({"name": source["name"], "rate": rate, "url": source["url"]})
            print(f"  ✓ {source['name']}: {rate}%")
        except Exception as exc:
            errors.append(f"{source['name']}: {exc}")
            print(f"  ✗ {source['name']}: {exc}", file=sys.stderr)

    if not results:
        print("All fetches failed — not overwriting existing data.", file=sys.stderr)
        sys.exit(1)

    # Sort highest rate first (leaderboard order)
    results.sort(key=lambda r: r["rate"], reverse=True)

    payload = {"updated": today, "rates": results}
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"\nWrote {OUTPUT} ({OUTPUT.stat().st_size} bytes)")

    if errors:
        print(f"\nPartial failures ({len(errors)}):", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
