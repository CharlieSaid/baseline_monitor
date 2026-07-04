"""Forbright Bank Growth Savings account APY."""

from scrapers.common import fetch, find_first_percent

NAME = "Forbright Growth Savings"
URL = "https://www.forbrightbank.com/stories/resources/growth-savings-product-guide/"
FALLBACK_URL = (
    "https://openaccount.forbrightbank.com/products"
    "?customerCategory=personal&productType=savings"
)
_GUIDE_PATTERNS = (
    r"Current APY</td><td>([\d]+\.[\d]+)%",
    r"Current APY[\s\S]{0,80}?([\d]+\.[\d]+)\s*%",
)
_PRODUCTS_PATTERN = r"([\d]+\.[\d]+)\s*%\s*annual percentage yield\s*\(APY\)"


def fetch_rate() -> float:
    html = fetch(URL)
    for pattern in _GUIDE_PATTERNS:
        rate = find_first_percent(html, pattern)
        if rate is not None:
            return rate

    html = fetch(FALLBACK_URL)
    rate = find_first_percent(html, _PRODUCTS_PATTERN)
    if rate is not None:
        return rate
    raise ValueError("Forbright Growth Savings rate not found")
