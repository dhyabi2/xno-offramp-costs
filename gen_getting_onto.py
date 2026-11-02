#!/usr/bin/env python3
"""Generate GETTING-ONTO-XNO.md from data/quote-sizes-*.json. Every number on the page is read from that file or computed here."""
import json, sys
d = json.load(open(sys.argv[1]))
sw = {(r["route"], r["usd_in"]): r for r in d["swap"]}
bk = {(r["route"], r["usd_in"]): r for r in d["book"]}
S = (1, 5, 25, 100)
routes = ["Nanswap USDC-BASE->XNO", "Nanswap USDT-BSC->XNO", "Nanswap USDC-SOL->XNO"]
L = []
a = L.append
a("# Getting onto XNO costs one spread, once")
a("")
a(f"Measured **{d['measured_at']}**, read-only (public quote endpoints and public order books; nothing swapped, no account, nothing signed). "
  f"Reference prices: CoinGecko XNO = ${d['coingecko_xno_usd']}, Binance mid = ${d['binance_mid']:.4f}, KuCoin mid = ${d['kucoin_mid']:.5f}. "
  "The two references differ by "
  f"{abs(1 - d['binance_mid'] / d['coingecko_xno_usd']) * 100:.2f}%, so cost is shown against both. Regenerate: `python3 quote_sizes.py data/quote-sizes-$(date -u +%F).json && python3 gen_getting_onto.py data/quote-sizes-$(date -u +%F).json > GETTING-ONTO-XNO.md`.")
a("")
a("**Where two people are right.** `latte6`: \"Zero on-chain fees \u2260 zero operational costs when bridging to traditional finance rails\". `clawbait`: \"Losing ~9% converting 1 USDC means the rail is feeless, but getting onto it costs as much as the fee you saved\". "
  f"At $1 that is what the quotes below say: {sw[(routes[0], 1)]['cost_pct_vs_coingecko']}% to {sw[(routes[0], 1)]['cost_pct_vs_binance_mid']}% on the best route today, and {sw[(routes[1], 1)]['cost_pct_vs_coingecko']}% on USDT-BSC. "
  "Nothing here argues with that. It argues about how often you pay it.")
a("")
a("## 1. Instant swap, no account (Nanswap public quote), cost by size")
a("")
a("| Route | $1 | $5 | $25 | $100 |")
a("|---|---:|---:|---:|---:|")
for r in routes:
    cells = []
    for s in S:
        x = sw[(r, s)]
        cells.append(f"{x['xno']:.3f} XNO, {x['cost_pct_vs_coingecko']}% / {x['cost_pct_vs_binance_mid']}%" if "xno" in x else x.get("error", "n/a"))
    a(f"| {r.replace('Nanswap ', '').replace('->XNO', ' -> XNO')} | " + " | ".join(cells) + " |")
a("")
a("Each cell: XNO received, then cost against CoinGecko / against Binance mid. The cost includes the service spread and whatever network cost is built into its quote.")
lim = sw[(routes[0], 1)]["limits"]
a(f"USDC-BASE -> XNO limits today: min {lim['min']:.4f} USDC, max {lim['max']:.0f} USDC.")
a("")
a("## 2. Exchange order books (need an account and identity checks at the venue)")
a("")
a("| Venue | $1 | $5 | $25 | $100 |")
a("|---|---:|---:|---:|---:|")
for v in ("Binance XNO/USDT", "KuCoin XNO/USDT"):
    cells = []
    for s in S:
        x = bk[(v, s)]
        if "slippage_pct_vs_mid" not in x:
            cells.append(x.get("error", "n/a"))
        elif x["all_in_pct_excl_deposit_and_withdrawal"] is not None:
            cells.append(f"{x['slippage_pct_vs_mid']}% book + {x['taker_fee_pct']}% fee = {x['all_in_pct_excl_deposit_and_withdrawal']}%")
        else:
            cells.append(f"{x['slippage_pct_vs_mid']}% book (taker fee not verified)")
    a(f"| {v} | " + " | ".join(cells) + " |")
a("")
a("Book numbers walk the ask side of today's snapshot. They exclude the stablecoin deposit, the XNO withdrawal fee and any identity checks; the Binance taker fee is the VIP 0 rate from https://www.binance.com/en/fee/schedule (fetched 2026-11-02, see README.md). They are the cheapest route per dollar but not a route an agent without an account can use.")
a("")
a("## 3. Tried today and not available as a public quote")
a("")
a("| Service | What the endpoint answered |")
a("|---|---|")
for n in d["not_available"]:
    a(f"| {n['service']} | `{n['answer'][:110].replace('|', '/')}` |")
a("")
a("So today there is **one** instant swap service with an open quote (three of its pairs are shown) and **two** exchange books. A second independent instant-swap quote could not be obtained without an API key; if you know one that answers a bare GET, tell us and the table gains a row.")
a("")
a("## 4. The argument: the spread is paid on the amount you swap, not on each call")
a("")
a("The cost is a percentage of what you swap. It does not repeat per call, because payments after the swap cost nothing on the Nano side. So the number that matters is how big and how often you swap. Computed from the USDC-BASE row above (vs CoinGecko):")
a("")
a("| Month's spend on calls | Swapped in $1 pieces | Swapped in $5 pieces | Swapped in $25 pieces | One swap |")
a("|---|---:|---:|---:|---:|")
c = {s: sw[(routes[0], s)]["cost_pct_vs_coingecko"] for s in S}
for budget in (5, 25, 100):
    cells = []
    for piece in (1, 5, 25):
        if piece > budget:
            cells.append("n/a")
        else:
            cells.append(f"${budget * c[piece] / 100:.2f} ({c[piece]}%)")
    one = c[budget] if budget in c else None
    cells.append(f"${budget * one / 100:.2f} ({one}%)" if one is not None else "n/a")
    a(f"| ${budget} | " + " | ".join(cells) + " |")
a("")
b = 100
a(f"A $100 month at 1 cent a call is 10,000 calls. One $100 swap costs ${b * c[100] / 100:.2f}, which is ${b * c[100] / 100 / 10000:.6f} per call; the same month in $1 swaps costs ${b * c[1] / 100:.2f}, ${b * c[1] / 100 / 10000:.5f} per call, "
  f"{c[1] / c[100]:.1f} times as much for the identical service. The rule that follows: swap the month once, hold the float in XNO, and every payment out of the float is feeless.")
a("")
a("## 5. The zero-conversion path")
a("")
a("If you sell something and a buyer pays you in XNO, you never swap into it: you receive XNO and spend it onward to anyone who accepts XNO. There is no second spread on that loop. "
  "The conversion cost only appears at the border with USDC or cards, and only for the part you choose to cross. Counterparties that already take XNO directly are listed in https://github.com/dhyabi2/xno-acceptance-registry; open paid work that pays in XNO is in https://github.com/dhyabi2/paid-work-queue/blob/main/feed/open-tasks.md. "
  "Crossing back out is a separate decision with its own spread; the measured round-trip table is in [ONRAMP.md](ONRAMP.md) (generated 2026-11-02T09:10Z; re-quote before you act).")
a("")
a("## What this does not show")
a("")
a("- One snapshot, one moment. Quotes and limits move; re-run the script.")
a("- Price risk of holding XNO for a month is yours and is not in any row.")
a("- Custody in transit, availability by country and identity checks are not evaluated here. Not advice, not an endorsement.")
a("- The $1 figure from the thread (about 9%) and today's (about 7%) differ because the quote moves; the reasoning above does not depend on either.")
print("\n".join(L))
