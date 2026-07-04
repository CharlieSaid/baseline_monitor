"""Bread Savings high-yield savings account APY."""

from scrapers.common import fetch, find_first_percent

NAME = "Bread Savings HYSA"
URL = "https://breadsavings.com/"
_FALLBACK_URL = "https://opensavings.breadfinancial.com/products"


def fetch_rate() -> float:
    html = fetch(URL)
    rate = find_first_percent(html, r"([\d]+\.[\d]+)\s*%\s*</span><sub>APY.*?HYSA")
    if rate is not None:
        return rate
    html = fetch(_FALLBACK_URL)
    rate = find_first_percent(html, r"High Yield Savings.*?([\d]+\.[\d]+)\s*%\s*APY")
    if rate is not None:
        return rate
    raise ValueError("Bread Savings HYSA rate not found")
