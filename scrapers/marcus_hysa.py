"""Marcus high-yield savings account APY."""

from scrapers.common import fetch, find_first_percent

NAME = "Marcus HYSA"
URL = "https://www.marcus.com/us/en/savings/high-yield-savings"


def fetch_rate() -> float:
    html = fetch(URL)
    for pattern in (
        r'font-size__46px">([\d]+\.[\d]+)\s*%\s*APY',
        r'([\d]+\.[\d]+)\s*%\s*APY(?! Rate Boost)',
    ):
        rate = find_first_percent(html, pattern)
        if rate is not None:
            return rate
    raise ValueError("Marcus HYSA rate not found")
