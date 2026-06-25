"""SoFi high-yield savings account APY."""

from scrapers.common import fetch, find_first_percent

NAME = "SoFi HYSA"
URL = "https://www.sofi.com/banking/savings-account/"


def fetch_rate() -> float:
    html = fetch(URL)
    rate = find_first_percent(html, r"([\d]+\.[\d]+)\s*%\s*APY")
    if rate is not None:
        return rate
    raise ValueError("SoFi HYSA rate not found")
