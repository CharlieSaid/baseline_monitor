#!/usr/bin/env python3
"""
fetch_rates.py — scrapes current savings rates and writes data/rates.json.

Sources:
  - T-Bill (4-week): TreasuryDirect auction results API
  - VMFXX:           Vanguard internal fund data API
  - HYSAs:           Each bank's public rate page

Run daily via GitHub Actions. Writes a ~200-byte JSON file.
"""

import json
import re
import sys
from datetime import date
from pathlib import Path
import urllib.request

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
    """4-week T-Bill high rate from the TreasuryDirect auction results API."""
    url = "https://www.treasurydirect.gov/TA_WS/securities/search?type=Bill&term=4-Week&pagesize=1&format=json"
    raw = fetch(url)
    data = json.loads(raw)
    if not data:
        raise ValueError("Empty response from TreasuryDirect API")
    # highDiscountRate is the annualized discount rate from the most recent auction
    rate = data[0].get("highDiscountRate") or data[0].get("highInvestmentRate")
    if rate is None:
        raise ValueError(f"Rate field missing from response: {data[0].keys()}")
    return round(float(rate), 2)


def fetch_vmfxx() -> float:
    """VMFXX 7-day SEC yield from Vanguard's internal fund data API."""
    url = "https://investor.vanguard.com/investment-products/money-markets/profile/api/VMFXX/overview"
    raw = fetch(url)
    data = json.loads(raw)
    # Path: fundProfile > fundManagement > [yields] > sevenDaySecYield
    yields = (
        data.get("fundProfile", {})
            .get("fundManagement", {})
            .get("yields", {})
    )
    rate = yields.get("sevenDaySecYield")
    if rate is None:
        raise ValueError(f"sevenDaySecYield not found in response")
    return round(float(rate), 2)


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

    # Ensure output directory exists
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

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