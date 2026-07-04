"""Forbright Bank Growth Savings account APY."""

from scrapers.common import fetch, find_first_percent

NAME = "Forbright Growth Savings"
URL = "https://www.forbrightbank.com/stories/resources/growth-savings-product-guide/"


def fetch_rate() -> float:
    html = fetch(URL)
    rate = find_first_percent(html, r"Current APY</td><td>([\d]+\.[\d]+)%")
    if rate is not None:
        return rate
    raise ValueError("Forbright Growth Savings rate not found")
