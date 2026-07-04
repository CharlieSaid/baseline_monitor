"""Synchrony Bank high-yield savings account APY."""

from scrapers.common import fetch, find_first_percent

NAME = "Synchrony HYSA"
URL = "https://www.synchronybank.com/banking/high-yield-savings/"
API_URL = "https://api.syf.com/v1/retailBank/products?serviceLevel=0000000"


def fetch_rate() -> float:
    raw = fetch(API_URL)
    rate = find_first_percent(
        raw, r'"displayCode"\s*:\s*"HYS"[\s\S]*?"maxAPY"\s*:\s*"([\d]+\.[\d]+)%"'
    )
    if rate is not None:
        return rate
    raise ValueError("Synchrony HYSA rate not found")
