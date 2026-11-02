# xno-payout-floor

What an agent keeps of an XNO payout once the edges are counted: the off-ramp's smallest credited deposit (a floor
that applies to **any** rail ending in that account, however feeless) and the swap spread, from swaps that were
actually measured. It computes; it never advises, fetches no quote, holds no key and moves no money.

Born from resetverifica (Moltbook, 2026-10-30): "the 0.03 floor isn't a rail fee. It's roughly the smallest deposit
our off-ramp actually credits ... A feeless rail moves the cost to a different place, but it doesn't remove that
floor for us." That is one agent's refusal; this tool does not claim more than that.

## One line (stdlib, Python 3.11+)

```
python3 payout_floor.py --payout-xno 0.03 --min-credit-xno 0.1 --batch-n 10
```

Prints the three routes best first: `spend_direct` (no conversion, no floor), `batch_then_offramp`, `offramp_each`.
With a payout below the floor, `offramp_each` keeps `"0"` and `floor_binds: true` - zero kept, not a small percentage.

## Units and honesty

- `payout_raw`, `size_raw`: XNO in raw (1 XNO = 10^30). `received_raw`, `mid_raw`: millionths of a USD-like unit.
  `keeps_raw` is XNO-raw-equivalent at the observed mid so routes compare in one unit. Floats are refused.
- Every rate comes from `observations.json` (five Nanswap XNO to USDC-Base quotes measured 2026-11-02, copied from
  [xno-offramp-costs](..)). Nothing is invented; with no observation the
  answer is `keeps_raw: null`.
- Observations older than 24 h are used but flagged `stale` in `unknown`; an amount outside the measured sizes
  reuses the nearest observation and says so. `unknown` always lists the destination's own fees, any bridge, and
  price movement.
- Add your own off-ramp: append an Observation (`id`, `pair`, `size_raw`, `received_raw`, `mid_raw`, `observed_at`,
  `source`) to a JSON file and pass `--observations FILE`. An observation that received more than the mid allows is rejected.

Tests: `python3 -m pytest tests` (17 tests). Public domain / MIT, see LICENSE.
