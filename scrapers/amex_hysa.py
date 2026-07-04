"""American Express high-yield savings account APY."""

from scrapers.common import fetch, find_first_percent

NAME = "American Express HYSA"
URL = "https://www.americanexpress.com/en-us/banking/online-savings/high-yield-savings-account/"
API_URL = (
    "https://daconsumershop.americanexpress.com"
    "/us/cardshop-api/api/v1/cps/content/banking/highYieldSavings"
)


def fetch_rate() -> float:
    body = fetch(API_URL)
    rate = find_first_percent(body, r'"apy"\s*:\s*"([\d]+\.[\d]+)"')
    if rate is not None:
        return rate
    raise ValueError("American Express HYSA rate not found")
