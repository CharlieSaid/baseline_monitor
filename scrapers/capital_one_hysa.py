"""Capital One 360 Performance Savings APY."""

import json
import urllib.request

from scrapers.common import find_first_percent

NAME = "Capital One HYSA"
URL = "https://www.capitalone.com/bank/savings-accounts/online-performance-savings-account/"
API_URL = "https://api.capitalone.com/deposits/products/~/search"
PSA_REGEX = (
    r'"productCode":"3800"[\s\S]*?"rateTiers"[\s\S]*?"annualizedPercentageYield":([\d]+(?:\.[\d]+)?)'
)


def fetch_rate() -> float:
    body = json.dumps({"include": ["RATES"], "isRenewableRate": True}).encode()
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "User-Agent": "rate-leaderboard/1.0",
            "Content-Type": "application/json",
            "Accept": "application/json;v=4",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    rate = find_first_percent(raw, PSA_REGEX)
    if rate is not None:
        return rate
    raise ValueError("Capital One HYSA rate not found")
