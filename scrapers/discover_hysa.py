"""Discover Online Savings account APY."""

from scrapers.common import fetch_json, find_first_percent

NAME = "Discover HYSA"
URL = "https://www.discover.com/online-banking/savings-account/"
RATES_API = "https://www.discoverbank.com/rates/legacy/featured.json?aff=NAT"


def fetch_rate() -> float:
    data = fetch_json(RATES_API)
    for item in data.get("dataset", []):
        if item.get("instrumentName") == "ONLINE SAVINGS":
            return round(float(item["apy"]), 2)
    raw = str(data)
    rate = find_first_percent(
        raw, r'"instrumentName"\s*:\s*"ONLINE SAVINGS"[\s\S]*?"apy"\s*:\s*([\d.]+)'
    )
    if rate is not None:
        return rate
    raise ValueError("Discover HYSA rate not found")
