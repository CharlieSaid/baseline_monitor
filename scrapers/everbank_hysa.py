"""EverBank Performance Savings account APY."""

from scrapers.common import fetch, find_first_percent

NAME = "EverBank Performance Savings"
URL = "https://www.everbank.com/banking/performance-savings"


def fetch_rate() -> float:
    html = fetch(URL)
    rate = find_first_percent(html, r'data-rate-prop="apy"[^>]*>([\d]+\.[\d]+)')
    if rate is not None:
        return rate
    raise ValueError("EverBank Performance Savings rate not found")
