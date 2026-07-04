"""Axos Bank Summit Savings account APY."""

from scrapers.common import fetch, find_first_percent

NAME = "Axos Summit Savings"
URL = "https://www.axosbank.com/personal/bank/savings-accounts/summit-savings"


def fetch_rate() -> float:
    html = fetch(URL)
    rate = find_first_percent(html, r"([\d]+\.[\d]+)\s*%\s*APY")
    if rate is not None:
        return rate
    raise ValueError("Axos Summit Savings rate not found")
