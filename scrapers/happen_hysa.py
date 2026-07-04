"""Happen Bank LevelUp Savings APY."""

from scrapers.common import fetch, find_first_percent

NAME = "Happen LevelUp Savings"
URL = "https://www.happen.com/personal-banking"


def fetch_rate() -> float:
    html = fetch(URL)
    rate = find_first_percent(html, r"LevelUp Rate.*?of ([\d]+\.[\d]+)\s*%")
    if rate is not None:
        return rate
    raise ValueError("Happen LevelUp Savings rate not found")
