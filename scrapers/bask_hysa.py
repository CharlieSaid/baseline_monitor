"""Bask Bank Interest Savings account APY."""

from scrapers.common import fetch, find_first_percent

NAME = "Bask Interest Savings"
URL = "https://baskbank.com/products/interest-savings-account"
ALT_URL = "https://baskbank.com/current-rates"


def fetch_rate() -> float:
    html = fetch(URL)
    rate = find_first_percent(html, r"Earn\s+([\d]+\.[\d]+)\s*%\s*Annual Percentage Yield")
    if rate is not None:
        return rate
    html = fetch(ALT_URL)
    rate = find_first_percent(
        html,
        r"Bask Interest Savings[\s\S]{0,500}?[\d]+\.[\d]+\s*%[\s\S]{0,100}?([\d]+\.[\d]+)\s*%",
    )
    if rate is not None:
        return rate
    raise ValueError("Bask Interest Savings rate not found")
