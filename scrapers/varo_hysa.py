"""Varo Bank Savings account APY."""

from scrapers.common import fetch, find_first_percent

NAME = "Varo Bank Savings"
URL = "https://www.varomoney.com/savings-account/"


def fetch_rate() -> float:
    html = fetch(URL)
    rate = find_first_percent(html, r"up to ([\d]+\.[\d]+)\s*%\s*APY")
    if rate is not None:
        return rate
    rate = find_first_percent(html, r"([\d]+\.[\d]+)\s*%\s*APY")
    if rate is not None:
        return rate
    raise ValueError("Varo Bank Savings rate not found")
