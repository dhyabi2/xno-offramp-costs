#!/usr/bin/env python3
import json
n = json.load(open('data/nanswap-2026-11-02.json')); d = json.load(open('data/depth-2026-11-02.json')); k = json.load(open('data/kucoin-currency-XNO-2026-11-02.json'))['data']['chains'][0]
bmid = d['venues']['binance']['mid']; cg = n['mid_price_usd_coingecko']
def rows(pair):
    s = ['| Size (USD at mid) | XNO -> %s: you receive | cost vs CoinGecko mid | cost vs Binance mid | %s -> XNO: cost vs CoinGecko mid |' % (pair, pair), '|---|---|---|---|---|']
    for r in n['rows']:
        if r['pair'] != pair: continue
        usd = r['size_usd_at_mid']; rec = r['out_received_usd']
        s.append('| $%s | %s %s (%s XNO sent) | %s%% (~$%s) | %.2f%% | %s%% |' % (usd, rec, pair.split('-')[0], r['out_xno_in'], r['out_cost_pct'], r['out_cost_usd'], (1 - rec / (r['out_xno_in'] * bmid)) * 100, r['in_cost_pct']))
    return '\n'.join(s)
cx = ['| Size (USD at mid) | Binance XNO/USDT: slippage vs book mid | KuCoin XNO/USDT: slippage vs book mid |', '|---|---|---|']
for i, u in enumerate((1, 5, 25, 100, 250)):
    cx.append('| $%s | %s%% | %s%% |' % (u, d['venues']['binance']['sells'][i]['slippage_vs_mid_pct'], d['venues']['kucoin']['sells'][i]['slippage_vs_mid_pct']))
lim = [r for r in n['rows'] if r['pair'] == 'USDC-BASE'][0]
txt = f'''# xno-offramp-costs

What it really costs to turn XNO into USDC/credits (and back), measured on **{n['measured_at']}**. Every figure below is generated from the JSON in `data/` by public, read-only calls (`measure.py`, `depth.py`); nothing was swapped or paid. Re-run them to refresh. Public domain (CC0).

**Not advice, not an endorsement.** Nothing here says any service is safe, solvent or available in your jurisdiction. Swap services and exchanges hold your funds in transit (custody) and exchanges usually need an account and identity checks; this page does not evaluate that.

## 1. Swap service quote: Nanswap (public API, no account)

Quotes from `https://api.nanswap.com/get-estimate` ({n['measured_at']}). Reference price: CoinGecko XNO = ${cg} (`{n['source_mid']}`); Binance book mid at the same time = ${bmid} (so the two references differ by {round((cg/bmid-1)*100,2)}%; both are shown). "Cost" = value lost against the reference, including the service spread and whatever network cost is built into the quote. Nanswap's FAQ says network costs for non-Nano assets are "included in the estimated price" and gives no percentage fee (https://nanswap.com/faq, fetched {n['measured_at'][:10]}).

### XNO -> USDC on Base
{rows('USDC-BASE')}

Limits (from `get-limits`, {n['measured_at'][:10]}): XNO -> USDC-BASE min {lim['limits_out_xno']['min']} XNO, max {lim['limits_out_xno']['max']} XNO; USDC-BASE -> XNO min {lim['limits_in_usd']['min']} USDC, max {lim['limits_in_usd']['max']:.0f} USDC.

### XNO -> USDT on BSC
{rows('USDT-BSC')}

### XNO -> USDC on Solana
{rows('USDC-SOL')}

**Reading it.** On this day the outbound cost fits roughly *about 4% of the amount plus about $0.30 fixed* (USDC-Base: $1 lost 31%, $250 lost 4.2%), while the inbound direction fits roughly *about 0.9% plus about $0.08*. Those two fits are descriptive of one snapshot, not a published fee schedule. An agent told us this leg "cost roughly 10%" matches the $5 row ({[r for r in n['rows'] if r['pair']=='USDC-BASE' and r['size_usd_at_mid']==5][0]['out_cost_pct']}%); it is only that bad for small sizes.

## 2. Exchange order books: slippage only

Selling XNO at market through the public XNO/USDT order book ({d['measured_at']}); `depth.py`. **Trading fees, USDT withdrawal fees and any account requirements are not included in these numbers.**
{chr(10).join(cx)}

Binance spread {d['venues']['binance']['spread_pct']}%, KuCoin spread {d['venues']['kucoin']['spread_pct']}%.

Fees I could verify:
- Binance regular user (VIP 0) spot fee: 0.100% maker / 0.100% taker, per https://www.binance.com/en/fee/schedule (fetched {d['measured_at'][:10]}).
- KuCoin XNO on the NANO chain: withdrawal min size {k['withdrawalMinSize']} XNO, withdrawal fee {k['withdrawalMinFee']} XNO, deposit min {k['depositMinSize']} XNO, deposits and withdrawals enabled (`https://api.kucoin.com/api/v3/currencies/XNO`, {d['measured_at'][:10]}). Nano transfers to an exchange cost no on-chain fee.
- **Could not verify:** KuCoin spot fee tier (page not retrievable), Binance/KuCoin USDT/USDC withdrawal fees by network, Kraken (no XNO pair or asset in its public API on this date: `Unknown asset pair` / `Unknown asset`), Gate (`XNO_USDT` pair invalid on its public API), regional availability (one forum report says USDT pairs are unavailable to EU users; unconfirmed).

A rough all-in for a $100 sale on a Binance-type venue is therefore 0.1% fee + ~0.16% slippage + the USDT withdrawal fee (unverified, not counted) and requires an account; compare with ~4.4% through the swap service above. Exchange routes need KYC and custody on the venue; the swap route needs neither an account but the quote spread is wider.

## 3. Hold-float and batching guide

1. **Spend XNO where XNO is accepted.** Every conversion above costs more than zero; sellers that quote in XNO directly never need it. See https://github.com/dhyabi2/xno-acceptance-registry (live-checked list).
2. **Hold a working float in XNO** sized to the paid calls you expect in a period (Nano transfers cost no fee, so many small moves are free). Convert only the part you must have in USDC/credits.
3. **Batch the conversion.** With the fixed part of the cost near $0.30 and the proportional part near 4% (swap service, this day), one $250 conversion lost about $10.5 against ten $25 conversions about $13.3 on the fitted figures; below about $5 the fixed part dominates (a $1 swap lost 31%). Do not convert below the point where the fixed part is a few percent of the amount.
4. **Do not convert overnight-by-habit.** Price risk on XNO is yours while you hold it; the order-book spread on the exchanges above was {d['venues']['binance']['spread_pct']}-{d['venues']['kucoin']['spread_pct']}%, and XNO moved from ${bmid} (Binance) to ${cg} (CoinGecko) between sources, so check a live quote right before swapping.
5. **Check limits first** (min/max above) and re-quote: every number on this page is a snapshot.

## Files
- `data/nanswap-{n['measured_at'][:10]}.json`, `data/depth-{n['measured_at'][:10]}.json`, `data/kucoin-currency-XNO-{n['measured_at'][:10]}.json` raw measurements
- `measure.py`, `depth.py` re-run to refresh; `gen_readme.py` regenerates this page
'''
open('README.md', 'w').write(txt)
