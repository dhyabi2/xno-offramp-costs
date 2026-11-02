#!/usr/bin/env python3
"""Market-sell walk through the public XNO/USDT order book on Binance and KuCoin (read-only GETs). Fees NOT included."""
import json, urllib.request, datetime, sys
def get(u): return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'xno-offramp-costs/0.1'}), timeout=20))
books = {'binance': ('https://api.binance.com/api/v3/depth?symbol=XNOUSDT&limit=100', lambda d: (d['bids'], d['asks'])),
         'kucoin': ('https://api.kucoin.com/api/v1/market/orderbook/level2_100?symbol=XNO-USDT', lambda d: (d['data']['bids'], d['data']['asks']))}
out = {'measured_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'), 'venues': {}}
for v, (u, f) in books.items():
    bids, asks = f(get(u)); bids = [(float(p), float(q)) for p, q in bids]; asks = [(float(p), float(q)) for p, q in asks]
    mid = (bids[0][0] + asks[0][0]) / 2; res = []
    for usd in (1, 5, 25, 100, 250):
        xno = usd / mid; need = xno; got = 0.0
        for p, q in bids:
            t = min(q, need); got += t * p; need -= t
            if need <= 1e-12: break
        res.append({'size_usd_at_mid': usd, 'xno_sold': round(xno, 4), 'filled': need <= 1e-9, 'usdt_received': round(got, 4) if need <= 1e-9 else None, 'slippage_vs_mid_pct': round((1 - got / usd) * 100, 3) if need <= 1e-9 else None})
    out['venues'][v] = {'source': u, 'best_bid': bids[0][0], 'best_ask': asks[0][0], 'mid': round(mid, 5), 'spread_pct': round((asks[0][0] / bids[0][0] - 1) * 100, 3), 'sells': res}
json.dump(out, open(sys.argv[1], 'w'), indent=1)
for v, x in out['venues'].items(): print(v, x['mid'], x['spread_pct'], [(r['size_usd_at_mid'], r['slippage_vs_mid_pct']) for r in x['sells']])
