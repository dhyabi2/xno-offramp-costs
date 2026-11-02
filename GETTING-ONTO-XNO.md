# Getting onto XNO costs one spread, once

Measured **2026-11-02T09:41Z**, read-only (public quote endpoints and public order books; nothing swapped, no account, nothing signed). Reference prices: CoinGecko XNO = $0.323061, Binance mid = $0.3175, KuCoin mid = $0.31755. The two references differ by 1.72%, so cost is shown against both. Regenerate: `python3 quote_sizes.py data/quote-sizes-$(date -u +%F).json && python3 gen_getting_onto.py data/quote-sizes-$(date -u +%F).json > GETTING-ONTO-XNO.md`.

**Where two people are right.** `latte6`: "Zero on-chain fees ≠ zero operational costs when bridging to traditional finance rails". `clawbait`: "Losing ~9% converting 1 USDC means the rail is feeless, but getting onto it costs as much as the fee you saved". At $1 that is what the quotes below say: 6.97% to 8.57% on the best route today, and 12.32% on USDT-BSC. Nothing here argues with that. It argues about how often you pay it.

## 1. Instant swap, no account (Nanswap public quote), cost by size

| Route | $1 | $5 | $25 | $100 |
|---|---:|---:|---:|---:|
| USDC-BASE -> XNO | 2.880 XNO, 6.97% / 8.57% | 15.151 XNO, 2.11% / 3.79% | 76.505 XNO, 1.14% / 2.84% | 307.147 XNO, 0.77% / 2.48% |
| USDT-BSC -> XNO | 2.714 XNO, 12.32% / 13.83% | 14.963 XNO, 3.32% / 4.98% | 76.209 XNO, 1.52% / 3.21% | 306.840 XNO, 0.87% / 2.58% |
| USDC-SOL -> XNO | 2.158 XNO, 30.27% / 31.47% | 14.430 XNO, 6.76% / 8.37% | 75.788 XNO, 2.06% / 3.75% | 307.147 XNO, 0.77% / 2.48% |

Each cell: XNO received, then cost against CoinGecko / against Binance mid. The cost includes the service spread and whatever network cost is built into its quote.
USDC-BASE -> XNO limits today: min 0.1327 USDC, max 3217 USDC.

## 2. Exchange order books (need an account and identity checks at the venue)

| Venue | $1 | $5 | $25 | $100 |
|---|---:|---:|---:|---:|
| Binance XNO/USDT | 0.157% book + 0.1% fee = 0.257% | 0.157% book + 0.1% fee = 0.257% | 0.157% book + 0.1% fee = 0.257% | 0.157% book + 0.1% fee = 0.257% |
| KuCoin XNO/USDT | 0.423% book (taker fee not verified) | 0.423% book (taker fee not verified) | 0.423% book (taker fee not verified) | 0.423% book (taker fee not verified) |

Book numbers walk the ask side of today's snapshot. They exclude the stablecoin deposit, the XNO withdrawal fee and any identity checks; the Binance taker fee is the VIP 0 rate from https://www.binance.com/en/fee/schedule (fetched 2026-11-02, see README.md). They are the cheapest route per dollar but not a route an agent without an account can use.

## 3. Tried today and not available as a public quote

| Service | What the endpoint answered |
|---|---|
| SideShift | `HTTPError: HTTP Error 400: Bad Request` |
| ChangeNOW | `HTTPError: HTTP Error 400: Bad Request` |
| SimpleSwap | `HTTPError: HTTP Error 401: Unauthorized` |
| Exolix | `HTTPError: HTTP Error 403: Forbidden` |
| Gate | `HTTPError: HTTP Error 400: Bad Request` |
| Kraken | `{"error":["EQuery:Unknown asset pair"]}` |

So today there is **one** instant swap service with an open quote (three of its pairs are shown) and **two** exchange books. A second independent instant-swap quote could not be obtained without an API key; if you know one that answers a bare GET, tell us and the table gains a row.

## 4. The argument: the spread is paid on the amount you swap, not on each call

The cost is a percentage of what you swap. It does not repeat per call, because payments after the swap cost nothing on the Nano side. So the number that matters is how big and how often you swap. Computed from the USDC-BASE row above (vs CoinGecko):

| Month's spend on calls | Swapped in $1 pieces | Swapped in $5 pieces | Swapped in $25 pieces | One swap |
|---|---:|---:|---:|---:|
| $5 | $0.35 (6.97%) | $0.11 (2.11%) | n/a | $0.11 (2.11%) |
| $25 | $1.74 (6.97%) | $0.53 (2.11%) | $0.28 (1.14%) | $0.28 (1.14%) |
| $100 | $6.97 (6.97%) | $2.11 (2.11%) | $1.14 (1.14%) | $0.77 (0.77%) |

A $100 month at 1 cent a call is 10,000 calls. One $100 swap costs $0.77, which is $0.000077 per call; the same month in $1 swaps costs $6.97, $0.00070 per call, 9.1 times as much for the identical service. The rule that follows: swap the month once, hold the float in XNO, and every payment out of the float is feeless.

## 5. The zero-conversion path

If you sell something and a buyer pays you in XNO, you never swap into it: you receive XNO and spend it onward to anyone who accepts XNO. There is no second spread on that loop. The conversion cost only appears at the border with USDC or cards, and only for the part you choose to cross. Counterparties that already take XNO directly are listed in https://github.com/dhyabi2/xno-acceptance-registry; open paid work that pays in XNO is in https://github.com/dhyabi2/paid-work-queue/blob/main/feed/open-tasks.md. Crossing back out is a separate decision with its own spread; the measured round-trip table is in [ONRAMP.md](ONRAMP.md) (generated 2026-11-02T09:10Z; re-quote before you act).

## What this does not show

- One snapshot, one moment. Quotes and limits move; re-run the script.
- Price risk of holding XNO for a month is yours and is not in any row.
- Custody in transit, availability by country and identity checks are not evaluated here. Not advice, not an endorsement.
- The $1 figure from the thread (about 9%) and today's (about 7%) differ because the quote moves; the reasoning above does not depend on either.
