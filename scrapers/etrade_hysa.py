"""E*TRADE Premium Savings account APY (Morgan Stanley Private Bank)."""

from scrapers.common import fetch, find_first_percent

NAME = "E*TRADE Premium Savings"
URL = "https://us.etrade.com/bank/premium-savings-account"


def fetch_rate() -> float:
    html = fetch(URL)
    rate = find_first_percent(html, r"([\d]+\.[\d]+)\s*%\s*Base Rate")
    if rate is not None:
        return rate
    raise ValueError("E*TRADE Premium Savings rate not found")
