"""4-week T-Bill rate from the Federal Reserve H.15 Data Download Program."""

import csv
import io
import re

from scrapers.common import fetch

NAME = "T-Bill (4-week)"
URL = "https://www.treasurydirect.gov/auctions/upcoming/"

# Series bf17364827e38702b42a58cf8eaa3f78 = TB/4WEEKS (4-week T-Bill)
H15_URL = (
    "https://www.federalreserve.gov/datadownload/Output.aspx"
    "?rel=H15&series=bf17364827e38702b42a58cf8eaa3f78"
    "&lastobs=10&filetype=csv&label=include&layout=seriescolumn"
)


def fetch_rate() -> float:
    """
    Returns the most recent non-ND daily observation from the Fed's official
    direct-download CSV endpoint.
    """
    raw = fetch(H15_URL)

    lines = raw.splitlines()
    data_start = 0
    for i, line in enumerate(lines):
        if line.startswith("\"Series Description\"") or line.startswith("Series Description"):
            data_start = i
            break

    reader = csv.reader(io.StringIO("\n".join(lines[data_start:])))
    rows = list(reader)

    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    for row in reversed(rows):
        if row and date_pattern.match(row[0].strip()):
            value = row[1].strip() if len(row) > 1 else ""
            if value and value.upper() != "ND":
                return round(float(value), 2)

    raise ValueError("4-week T-Bill rate not found in H.15 CSV")
