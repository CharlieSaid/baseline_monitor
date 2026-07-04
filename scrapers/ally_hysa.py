"""Ally Bank high-yield savings account APY."""

import urllib.request

from scrapers.common import find_first_percent

NAME = "Ally HYSA"
URL = "https://www.ally.com/bank/online-savings-account/"
RATES_API = "https://secure.ally.com/acs/products/temporary/competitor?format=json"
_API_KEY = "TMqqqyuyVeNnD1HTgvsNu6lulUHL9ksc"


def fetch_rate() -> float:
    req = urllib.request.Request(
        RATES_API,
        headers={"User-Agent": "rate-leaderboard/1.0", "api-key": _API_KEY},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    rate = find_first_percent(
        raw,
        r'"bankName":"Ally Bank".{0,200}"termId":"OSAV-0M".{0,200}"apy":([\d.]+)',
    )
    if rate is not None:
        return rate
    raise ValueError("Ally HYSA rate not found")
