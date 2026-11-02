# xno-offramp-costs

What it really costs to turn XNO into USDC/credits (and back), measured on **2026-11-02T06:10Z**. Every figure below is generated from the JSON in `data/` by public, read-only calls (`measure.py`, `depth.py`); nothing was swapped or paid. Re-run them to refresh. Public domain (CC0).

**Not advice, not an endorsement.** Nothing here says any service is safe, solvent or available in your jurisdiction. Swap services and exchanges hold your funds in transit (custody) and exchanges usually need an account and identity checks; this page does not evaluate that.

**Getting onto XNO** (USDC -> XNO at $1/$5/$25/$100, why the spread is paid once): [GETTING-ONTO-XNO.md](GETTING-ONTO-XNO.md). Into-XNO round trip and monthly arithmetic: [ONRAMP.md](ONRAMP.md).

## 1. Swap service quote: Nanswap (public API, no account)

Quotes from `https://api.nanswap.com/get-estimate` (2026-11-02T06:10Z). Reference price: CoinGecko XNO = $0.325352 (`https://api.coingecko.com/api/v3/simple/price?ids=nano&vs_currencies=usd`); Binance book mid at the same time = $0.3205 (so the two references differ by 1.51%; both are shown). "Cost" = value lost against the reference, including the service spread and whatever network cost is built into the quote. Nanswap's FAQ says network costs for non-Nano assets are "included in the estimated price" and gives no percentage fee (https://nanswap.com/faq, fetched 2026-11-02).

### XNO -> USDC on Base
| Size (USD at mid) | XNO -> USDC-BASE: you receive | cost vs CoinGecko mid | cost vs Binance mid | USDC-BASE -> XNO: cost vs CoinGecko mid |
|---|---|---|---|---|
| $1 | 0.687714 USDC (3.0736 XNO sent) | 31.23% (~$0.3123) | 30.19% | 9.5% |
| $5 | 4.518349 USDC (15.368 XNO sent) | 9.63% (~$0.4817) | 8.27% | 2.8% |
| $25 | 23.671497 USDC (76.8399 XNO sent) | 5.31% (~$1.3285) | 3.88% | 1.46% |
| $100 | 95.639992 USDC (307.3594 XNO sent) | 4.36% (~$4.36) | 2.91% | 1.01% |
| $250 | 239.489896 USDC (768.3985 XNO sent) | 4.2% (~$10.5101) | 2.75% | 0.97% |

Limits (from `get-limits`, 2026-11-02): XNO -> USDC-BASE min 1.90063 XNO, max 9360.37441 XNO; USDC-BASE -> XNO min 0.1852361 USDC, max 3299 USDC.

### XNO -> USDT on BSC
| Size (USD at mid) | XNO -> USDT-BSC: you receive | cost vs CoinGecko mid | cost vs Binance mid | USDT-BSC -> XNO: cost vs CoinGecko mid |
|---|---|---|---|---|
| $1 | 0.8412401 USDT (3.0736 XNO sent) | 15.88% (~$0.1588) | 14.60% | 14.86% |
| $5 | 4.6696977 USDT (15.368 XNO sent) | 6.61% (~$0.3303) | 5.19% | 4.01% |
| $25 | 23.8119551 USDT (76.8399 XNO sent) | 4.75% (~$1.188) | 3.31% | 1.84% |
| $100 | 95.8379 USDT (307.3594 XNO sent) | 4.16% (~$4.1621) | 2.71% | 1.1% |
| $250 | 239.8348 USDT (768.3985 XNO sent) | 4.07% (~$10.1652) | 2.61% | 1.06% |

### XNO -> USDC on Solana
| Size (USD at mid) | XNO -> USDC-SOL: you receive | cost vs CoinGecko mid | cost vs Binance mid | USDC-SOL -> XNO: cost vs CoinGecko mid |
|---|---|---|---|---|
| $1 | 0.619531 USDC (3.0736 XNO sent) | 38.05% (~$0.3805) | 37.11% | 32.76% |
| $5 | 4.450389 USDC (15.368 XNO sent) | 10.99% (~$0.5496) | 9.64% | 7.45% |
| $25 | 23.604647 USDC (76.8399 XNO sent) | 5.58% (~$1.3954) | 4.15% | 2.39% |
| $100 | 95.589992 USDC (307.3594 XNO sent) | 4.41% (~$4.41) | 2.96% | 1.01% |
| $250 | 239.439896 USDC (768.3985 XNO sent) | 4.22% (~$10.5601) | 2.77% | 0.97% |

**Reading it.** On this day the outbound cost fits roughly *about 4% of the amount plus about $0.30 fixed* (USDC-Base: $1 lost 31%, $250 lost 4.2%), while the inbound direction fits roughly *about 0.9% plus about $0.08*. Those two fits are descriptive of one snapshot, not a published fee schedule. An agent told us this leg "cost roughly 10%" matches the $5 row (9.63%); it is only that bad for small sizes.

## 2. Exchange order books: slippage only

Selling XNO at market through the public XNO/USDT order book (2026-11-02T06:11Z); `depth.py`. **Trading fees, USDT withdrawal fees and any account requirements are not included in these numbers.**
| Size (USD at mid) | Binance XNO/USDT: slippage vs book mid | KuCoin XNO/USDT: slippage vs book mid |
|---|---|---|
| $1 | 0.156% | 0.389% |
| $5 | 0.156% | 0.389% |
| $25 | 0.156% | 0.389% |
| $100 | 0.156% | 0.43% |
| $250 | 0.156% | 0.65% |

Binance spread 0.313%, KuCoin spread 0.782%.

Fees I could verify:
- Binance regular user (VIP 0) spot fee: 0.100% maker / 0.100% taker, per https://www.binance.com/en/fee/schedule (fetched 2026-11-02).
- KuCoin XNO on the NANO chain: withdrawal min size 1.34 XNO, withdrawal fee 0.67 XNO, deposit min 0.05 XNO, deposits and withdrawals enabled (`https://api.kucoin.com/api/v3/currencies/XNO`, 2026-11-02). Nano transfers to an exchange cost no on-chain fee.
- **Could not verify:** KuCoin spot fee tier (page not retrievable), Binance/KuCoin USDT/USDC withdrawal fees by network, Kraken (no XNO pair or asset in its public API on this date: `Unknown asset pair` / `Unknown asset`), Gate (`XNO_USDT` pair invalid on its public API), regional availability (one forum report says USDT pairs are unavailable to EU users; unconfirmed).

A rough all-in for a $100 sale on a Binance-type venue is therefore 0.1% fee + ~0.16% slippage + the USDT withdrawal fee (unverified, not counted) and requires an account; compare with ~4.4% through the swap service above. Exchange routes need KYC and custody on the venue; the swap route needs neither an account but the quote spread is wider.

## 3. Hold-float and batching guide

1. **Spend XNO where XNO is accepted.** Every conversion above costs more than zero; sellers that quote in XNO directly never need it. See https://github.com/dhyabi2/xno-acceptance-registry (live-checked list).
2. **Hold a working float in XNO** sized to the paid calls you expect in a period (Nano transfers cost no fee, so many small moves are free). Convert only the part you must have in USDC/credits.
3. **Batch the conversion.** With the fixed part of the cost near $0.30 and the proportional part near 4% (swap service, this day), one $250 conversion lost about $10.5 against ten $25 conversions about $13.3 on the fitted figures; below about $5 the fixed part dominates (a $1 swap lost 31%). Do not convert below the point where the fixed part is a few percent of the amount.
4. **Do not convert overnight-by-habit.** Price risk on XNO is yours while you hold it; the order-book spread on the exchanges above was 0.313-0.782%, and XNO moved from $0.3205 (Binance) to $0.325352 (CoinGecko) between sources, so check a live quote right before swapping.
5. **Check limits first** (min/max above) and re-quote: every number on this page is a snapshot.

## The other direction
[ONRAMP.md](ONRAMP.md): USDC/USDT -> XNO at $1, $10, $100, $1000 with round-trip loss and a swap-once-a-month calculation (measured 2026-11-02T09:10Z).

## Files
- `data/nanswap-2026-11-02.json`, `data/depth-2026-11-02.json`, `data/kucoin-currency-XNO-2026-11-02.json` raw measurements
- `measure.py`, `depth.py` re-run to refresh; `gen_readme.py` regenerates this page

## Payout floor calculator

`payout-floor/` computes what a payout keeps after an off-ramp minimum and these measured spreads: `python3 payout-floor/payout_floor.py --payout-xno 0.03 --min-credit-xno 0.1`. Stdlib, 17 tests.
