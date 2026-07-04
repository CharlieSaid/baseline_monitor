"""Barclays US Online Savings account APY."""

from scrapers.common import fetch_json

NAME = "Barclays HYSA"
URL = "https://banking.barclaysus.com/online-savings"
RATES_URL = "https://banking.barclaysus.com/.rest/api/rates/get?id=3000-0"


def fetch_rate() -> float:
    data = fetch_json(RATES_URL)
    for product in data.get("products", []):
        if product.get("type") == "3000":
            return round(float(product["apy"]) * 100, 2)
    raise ValueError("Barclays HYSA rate not found")
