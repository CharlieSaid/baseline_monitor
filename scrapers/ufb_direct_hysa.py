"""UFB Direct Portfolio Savings APY."""

from scrapers.common import fetch, find_first_percent

NAME = "UFB Direct Portfolio Savings"
URL = "https://www.ufbdirect.com/savings"


def fetch_rate() -> float:
    html = fetch(URL)
    rate = find_first_percent(
        html,
        r"Portfolio Savings.*?<strong>([\d]+\.[\d]+)\s*%</strong>\s*APY",
    )
    if rate is not None:
        return rate
    raise ValueError("UFB Direct Portfolio Savings rate not found")
