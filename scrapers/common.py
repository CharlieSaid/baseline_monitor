"""Shared HTTP and parsing helpers for rate scrapers."""

import json
import re
import urllib.request


def fetch(url: str, timeout: int = 10) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "rate-leaderboard/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_json(url: str, timeout: int = 10) -> object:
    raw = fetch(url, timeout=timeout)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON from {url}") from exc


def find_first_percent(html: str, pattern: str) -> float | None:
    """Return the first float matching `pattern` in `html`, or None."""
    m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
    if m:
        try:
            return round(float(m.group(1)), 2)
        except ValueError:
            return None
    return None
