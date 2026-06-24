#!/usr/bin/env python3
"""
fetch_rates.py — fetches current savings rates and writes data/rates.json.

Sources:
  - T-Bill (4-week): Federal Reserve H.15 Data Download Program (official CSV)
  - VMFXX:           Yahoo Finance fund summary (widely-used, stable endpoint)
  - HYSAs:           Each bank's public rate page

Run daily via GitHub Actions. Writes a ~200-byte JSON file.
"""

import csv
import io
import json
import re
import sys
from datetime import date
from pathlib import Path
import urllib.request
import yfinance as yf

OUTPUT = Path(__file__).parent / "data" / "rates.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fetch(url: str, timeout: int = 10) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "rate-leaderboard/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def find_first_percent(html: str, pattern: str) -> float | None:
    """Return the first float matching `pattern` in `html`, or None."""
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
    """
    4-week T-Bill secondary-market rate from the Fed's H.15 Data Download
    Program — the official 'direct download for automated systems' URL.
    Returns the most recent non-ND daily observation.
    """
    # Series bf17364827e38702b42a58cf8eaa3f78 = TB/4WEEKS (4-week T-Bill)
    url = (
        "https://www.federalreserve.gov/datadownload/Output.aspx"
        "?rel=H15&series=bf17364827e38702b42a58cf8eaa3f78"
        "&lastobs=10&filetype=csv&label=include&layout=seriescolumn"
    )
    raw = fetch(url)

    # The CSV has metadata rows before the header; skip lines until we find
    # a line starting with "Series Description" or the date header.
    lines = raw.splitlines()
    data_start = 0
    for i, line in enumerate(lines):
        if line.startswith("\"Series Description\"") or line.startswith("Series Description"):
            data_start = i
            break

    reader = csv.reader(io.StringIO("\n".join(lines[data_start:])))
    rows = list(reader)

    # rows[0] = header labels, rows[1] = series IDs, rows[2] = units, etc.
    # Find the row index where date/value data begins (rows whose first cell
    # looks like a date: YYYY-MM-DD).
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    for row in reversed(rows):
        if row and date_pattern.match(row[0].strip()):
            value = row[1].strip() if len(row) > 1 else ""
            if value and value.upper() != "ND":
                return round(float(value), 2)

    raise ValueError("4-week T-Bill rate not found in H.15 CSV")

def fetch_vmfxx() -> float:
    """Fetch VMFXX 7-day yield using yfinance."""
    ticker = yf.Ticker("VMFXX")
    info = ticker.info
    
    # Yahoo often puts it under one of these keys for money market funds
    yield_pct = (
        info.get("sevenDayYield") or           # sometimes present
        info.get("yield") or
        info.get("trailingAnnualDividendYield") or
        info.get("dividendYield")
    )
    
    if yield_pct is not None:
        # Convert to percentage if it's a decimal
        if yield_pct < 1:  
            yield_pct *= 100
        return round(float(yield_pct), 2)
    
    raise ValueError("7-day yield not found in yfinance response for VMFXX")


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