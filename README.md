# RWA Oracle Agent

Publishes tokenized-stock (RWA) price feeds to the Technocore network as a
signed contribution under a local Ed25519 DID.

Fetches live prices for Ondo-tokenized equities/ETFs (NVDA, MSTR, SPY, QQQ, IVV)
from CoinGecko, validates them (bounds + freshness), and prints an
approval-gated publish command. The agent **never** touches the identity
passphrase — publishing is always run by the human.

## Usage

```bash
python3 oracle_agent.py            # fetch + validate + print feed
python3 oracle_agent.py --publish  # also print the exact `say` command
```

Then run the printed command with your Technocore CLI:

```bash
~/Flop/.venv/bin/python ~/Flop/technocore_agent.py say lobby "<feed message>"
```

## Design rules
- Publishing is approval-gated; no automatic writes or retries.
- Sanity bounds (1 USD – 5M USD) and 1h freshness check on every quote.
- DID is public by design; no secrets in this repo.

DID: did:key:z6MkttCoDfbqmsviPyc4kz9dpzkVxtfwgEh797WzEbSpq16U
