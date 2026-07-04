"""Western Alliance Bank High-Yield Savings Premier APY."""

from scrapers.common import fetch, find_first_percent

NAME = "Western Alliance HYSA"
URL = "https://www.westernalliancebancorporation.com/personal-banking/high-yield-savings-account"


def fetch_rate() -> float:
    html = fetch(URL)
    rate = find_first_percent(html, r"([\d]+\.[\d]+)\s*%\s*APY")
    if rate is not None:
        return rate
    raise ValueError("Western Alliance HYSA rate not found")
