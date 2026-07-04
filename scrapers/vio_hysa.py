"""Vio Bank Online Savings account APY."""

import urllib.request

from scrapers.common import find_first_percent

NAME = "Vio Bank Online Savings"
URL = "https://www.viobank.com/online-savings-account"
_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _fetch_browser(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": _BROWSER_UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_rate() -> float:
    html = _fetch_browser(URL)
    for pattern in (
        r'id="rate"[^>]*value="([\d.]+)"',
        r'Online Savings Account APY:\s*([\d.]+)%',
        r'([\d]+\.[\d]+)\s*%\s*APY',
    ):
        rate = find_first_percent(html, pattern)
        if rate is not None:
            return rate
    raise ValueError("Vio Bank Online Savings rate not found")
