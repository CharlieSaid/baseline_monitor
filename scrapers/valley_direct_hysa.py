"""Valley Direct high-yield savings account APY."""

from scrapers.common import fetch, find_first_percent

NAME = "Valley Direct HYSA"
URL = "https://www.valleydirect.com/Savings"


def fetch_rate() -> float:
    html = fetch(URL)
    rate = find_first_percent(html, r'"HYSA-standard":"([\d]+\.[\d]+)"')
    if rate is not None:
        return rate
    raise ValueError("Valley Direct HYSA rate not found")
