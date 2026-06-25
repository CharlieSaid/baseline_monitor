"""Rate scrapers — one module per data source."""

from scrapers import marcus_hysa, sofi_hysa, tbill_4week, vmfxx

SOURCES = [
    tbill_4week,
    vmfxx,
    sofi_hysa,
    marcus_hysa,
]

__all__ = ["SOURCES", "marcus_hysa", "sofi_hysa", "tbill_4week", "vmfxx"]
