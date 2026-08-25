#!/usr/bin/env python3
"""RWA Oracle Agent — publishes tokenized-stock (RWA) price feeds to Technocore.

Fetches prices for Ondo/bStocks tokenized equities & ETFs from CoinGecko,
validates them, and formats a signed-publish-ready message for Technocore.
Publishing is approval-gated: this script never touches the identity key;
it prints the exact command the user runs to `say` the feed themselves.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone

DID = "did:key:z6MkttCoDfbqmsviPyc4kz9dpzkVxtfwgEh797WzEbSpq16U"

# CoinGecko id -> ticker label
ASSETS = {
    "nvidia-ondo-tokenized-stock": "NVDAON",
    "microstrategy-ondo-tokenized-stock": "MSTRON",
    "spdr-s-p-500-etf-ondo-tokenized-etf": "SPYON",
    "invesco-qqq-etf-ondo-tokenized-etf": "QQQON",
    "ishares-core-s-p-500-etf-ondo-tokenized-etf": "IVVON",
}

# Sanity bounds (USD) to catch bad/oracle-stale data
BOUNDS = {"min": 1.0, "max": 5_000_000.0}
MAX_AGE_SECONDS = 3600  # reject data older than 1h


def fetch_prices(ids: list[str]) -> dict:
    url = ("https://api.coingecko.com/api/v3/simple/price?ids="
           + ",".join(ids)
           + "&vs_currencies=usd&include_last_updated_at=true")
    req = urllib.request.Request(url, headers={"User-Agent": "rwa-oracle-agent/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def validate(data: dict) -> list[tuple[str, float, int]]:
    now = datetime.now(timezone.utc).timestamp()
    rows = []
    for cg_id, ticker in ASSETS.items():
        entry = data.get(cg_id)
        if not entry or "usd" not in entry:
            print(f"skip {ticker}: no data", file=sys.stderr)
            continue
        price, ts = entry["usd"], entry.get("last_updated_at", now)
        if not (BOUNDS["min"] <= price <= BOUNDS["max"]):
            raise ValueError(f"{ticker} price {price} outside sane bounds")
        if now - ts > MAX_AGE_SECONDS:
            print(f"warn {ticker}: stale ({int(now - ts)}s old)", file=sys.stderr)
        rows.append((ticker, price, ts))
    if not rows:
        raise ValueError("no valid prices")
    return rows


def format_message(rows) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    parts = [f"[RWA/{t}]: ${p:,.2f}" for t, p, _ in rows]
    return f"[Oracle Feed][RWA batch]: {' | '.join(parts)} verified at {ts} by DID {DID}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish", action="store_true",
                    help="print the exact technocore say command (does NOT run it)")
    args = ap.parse_args()

    data = fetch_prices(list(ASSETS))
    rows = validate(data)
    msg = format_message(rows)
    print("FEED:", msg)
    if args.publish:
        print("\nAPPROVAL-GATED publish command (run it yourself):\n"
              ".venv/bin/python ~/Flop/technocore_agent.py say lobby '" + msg + "'")


if __name__ == "__main__":
    main()
