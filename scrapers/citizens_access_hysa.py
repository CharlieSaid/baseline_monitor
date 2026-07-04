"""Citizens Access Online Savings account APY."""

import json
import urllib.request

from scrapers.common import fetch_json, find_first_percent

NAME = "Citizens Access HYSA"
URL = "https://www.secure.citizensaccess.com/Citizens/"
RATE_SHEET_URL = (
    "https://www.secure.citizensaccess.com/Citizens/customer-service/rate-sheet"
)
# secure.citizensaccess.com is Akamai-protected; same rates JSON is public here.
RATES_JSON = "https://www.citizensbank.com/assets/CB_resources/json/rates/cax.json"

_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_HTML_TIER_APY = r"\$5,000\.00\s*\+[^|]{0,200}?\|\s*[\d.]+\s*%\s*\|\s*([\d.]+)\s*%"
_JSON_TIER_APY = r'"interestAPY":"([\d.]+)%"[^}]*"rateDescription":"TERM2"'


def _fetch_browser(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": _BROWSER_UA})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_rate() -> float:
    for page_url in (RATE_SHEET_URL, URL):
        try:
            rate = find_first_percent(_fetch_browser(page_url), _HTML_TIER_APY)
            if rate is not None:
                return rate
        except Exception:
            pass

    for brand in fetch_json(RATES_JSON):
        for region in brand.get("BrandData", []):
            for product in region.get("RegionData", {}).get("rates", []):
                if product.get("productDesc") != "SAVINGS":
                    continue
                blob = json.dumps(product, separators=(",", ":"))
                rate = find_first_percent(blob, _JSON_TIER_APY)
                if rate is not None:
                    return rate

    raise ValueError("Citizens Access HYSA rate not found")
