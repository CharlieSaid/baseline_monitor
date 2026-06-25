"""VMFXX net yield from Vanguard (7-day SEC yield minus expense ratio)."""

import json
import re

from scrapers.common import fetch, fetch_json

NAME = "VMFXX"
TICKER = "vmfxx"
URL = (
    "https://investor.vanguard.com/investment-products/mutual-funds/profile/vmfxx#overview"
)
API_BASE = f"https://investor.vanguard.com/vmf/api/{TICKER}"


def _sec_yield_from_price(price_data: object) -> float | None:
    if not isinstance(price_data, dict):
        return None
    current_price = price_data.get("currentPrice")
    if not isinstance(current_price, dict):
        return None
    yield_info = current_price.get("yield")
    if not isinstance(yield_info, dict):
        return None
    yield_pct = yield_info.get("yieldPct")
    if yield_pct is None:
        return None
    return float(yield_pct)


def _expense_ratio(expense_data: object) -> float | None:
    if not isinstance(expense_data, dict):
        return None
    expense_ratio = expense_data.get("expenseRatio")
    if expense_ratio is None:
        return None
    return float(expense_ratio)


def _expense_from_profile_html(html: str) -> float | None:
    match = re.search(
        r'<script id="fundProfileData" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    fund_profile = data.get("fundProfile") if isinstance(data, dict) else None
    if not isinstance(fund_profile, dict):
        return None
    expense_ratio = fund_profile.get("expenseRatio")
    if expense_ratio is None:
        return None
    return float(expense_ratio)


def fetch_rate() -> float:
    """
    Uses Vanguard's public vmf/api JSON endpoints (same data as the profile page),
    then subtracts the expense ratio from the 7-day SEC yield.
    """
    price_data = fetch_json(f"{API_BASE}/price")
    yield_pct = _sec_yield_from_price(price_data)
    if yield_pct is None:
        raise ValueError("7-day SEC yield not found in Vanguard VMFXX price API")

    expense_pct = None
    try:
        expense_data = fetch_json(f"{API_BASE}/expense")
        expense_pct = _expense_ratio(expense_data)
    except Exception:
        expense_pct = None

    if expense_pct is None:
        html = fetch(URL.split("#", 1)[0])
        expense_pct = _expense_from_profile_html(html)

    if expense_pct is None:
        raise ValueError("Expense ratio not found for Vanguard VMFXX")

    net_yield = yield_pct - expense_pct
    return round(max(net_yield, 0.0), 2)
