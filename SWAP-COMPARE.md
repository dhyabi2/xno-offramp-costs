# USDC to XNO: instant swap vs four public order books, at 1 / 25 / 100 USD

Measured **2026-11-02T11:23Z** by `compare_providers.py` (read-only public GETs; nothing swapped, no account used). Raw: `data/compare-2026-11-02.json`. Reference price: CoinGecko XNO.

CoinGecko XNO = $0.319885.

| Provider | USD in | XNO out | Cost vs CoinGecko | Round trip loss (book/quote only, no fees) |
|---|---|---|---|---|
| Nanswap swap (USDC-BASE) | 1 | 2.8697 | 7.58% | 36.48% |
| Nanswap swap (USDC-BASE) | 25 | 76.6116 | 1.31% | 6.57% |
| Nanswap swap (USDC-BASE) | 100 | 307.631 | 0.93% | 5.33% |
| Binance XNO/USDT book | 1 | 3.1447 | -1.27% | 0.63% |
| Binance XNO/USDT book | 25 | 78.6164 | -1.27% | 0.63% |
| Binance XNO/USDT book | 100 | 314.4654 | -1.27% | 0.63% |
| KuCoin XNO/USDT book | 1 | 3.1496 | -1.43% | 0.76% |
| KuCoin XNO/USDT book | 25 | 78.7402 | -1.43% | 0.76% |
| KuCoin XNO/USDT book | 100 | 314.2328 | -1.2% | 0.99% |
| Kraken NANO/USD book | 1 | 3.0729 | 1.04% | 0.67% |
| Kraken NANO/USD book | 25 | 76.8217 | 1.04% | 0.67% |
| Kraken NANO/USD book | 100 | 307.2867 | 1.04% | 0.67% |
| Gate NANO/USDT book | 1 | 3.0912 | 0.45% | 2.75% |
| Gate NANO/USDT book | 25 | 77.2798 | 0.45% | 2.77% |
| Gate NANO/USDT book | 100 | 309.119 | 0.45% | 2.78% |

## How to read it
- **Negative cost** means the book price is below the CoinGecko reference (CoinGecko lags by one to two percent against Binance and KuCoin books: see ONRAMP.md, which shows the same gap). Compare providers with each other, not against the reference.
- **Fees are not in the table.** Verified earlier (README.md): Binance VIP 0 spot fee 0.10%; KuCoin XNO withdrawal 0.67 XNO. Kraken and Gate fee schedules and the USDT/USD deposit and withdrawal costs were not verified, and every book route needs an account with identity checks and custody on the venue. Kraken NANO/USD takes USD; Gate and Binance and KuCoin take USDT, so a USDC holder pays one more conversion first.
- **The swap route is the only one with no account**, and it is the one with a size-dependent cost: about 8% at 1 USD, about 2% at 25 USD, about 1.6% at 100 USD, versus roughly 0.6 to 1.7% on the books at every size here.
- **Effective floor.** The instant swap has a minimum (0.14098 USDC on the day of ONRAMP.md) and a fixed part inside the quote, so a per-call top-up of cents is impossible and a 1 USD swap loses about a third on the round trip. The books have no fixed part in the quote, but the account, the deposit and the withdrawal fee (0.67 XNO at KuCoin, about 0.2 USD) put a floor of a few tens of cents on each move. Either way: swap once for the month's float (ONRAMP.md section 4), then pay from XNO, which is feeless.
- Not advice, not an endorsement. One snapshot; re-run before relying on it.

## Reproduce
```sh
python3 compare_providers.py data/compare-$(date -u +%F).json
```
