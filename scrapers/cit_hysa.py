"""CIT Bank Platinum Savings APY."""

import urllib.parse

from scrapers.common import fetch_json

NAME = "CIT Bank Platinum Savings"
URL = "https://www.cit.com/cit-bank/platinum-savings"


def fetch_rate() -> float:
    query = (
        'query { copyBlockProductBank(id: "74BOqDu31jnKnm1V1enZLE", preview: false) '
        "{ ratesCollection { items { apy } } } }"
    )
    api = (
        "https://graphql.contentful.com/content/v1/spaces/9j7wv5nnfw5f?"
        + urllib.parse.urlencode({
            "access_token": "zUw-Dj57TJuVf_9ZEjX2tKEU1K4ua8EpRoq8eU6H5DI",
            "query": query,
        })
    )
    items = fetch_json(api)["data"]["copyBlockProductBank"]["ratesCollection"]["items"]
    return round(max(float(item["apy"]) for item in items), 2)
