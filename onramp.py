#!/usr/bin/env python3
"""Cost of getting INTO XNO (USDC -> XNO) at $1/$10/$100/$1000, plus the round trip, today. Read-only GETs; no swap is created.
Usage: python3 onramp.py data/onramp-YYYY-MM-DD.json"""
import json, urllib.request, datetime, sys
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'xno-offramp-costs/0.2'}), timeout=25))
mid_cg = get('https://api.coingecko.com/api/v3/simple/price?ids=nano&vs_currencies=usd')['nano']['usd']
bk = get('https://api.binance.com/api/v3/depth?symbol=XNOUSDT&limit=1000')
bid0, ask0 = float(bk['bids'][0][0]), float(bk['asks'][0][0]); mid_bn = (bid0 + ask0) / 2
def book_buy(usd):  # walk asks spending usd of USDT; returns XNO bought (before the 0.1% fee) or None if book ended
    left, got = usd, 0.0
    for p, q in bk['asks']:
        p, q = float(p), float(q); take = min(left, p * q); got += take / p; left -= take
        if left <= 1e-9: return got
    return None
rows = []
for pair in ('USDC-BASE', 'USDT-BSC'):
    lim = get(f'https://api.nanswap.com/get-limits?from={pair}&to=XNO')
    for usd in (1, 10, 100, 1000):
        i = get(f'https://api.nanswap.com/get-estimate?from={pair}&to=XNO&amount={usd}')
        r = {'pair': pair, 'usd_in': usd, 'xno_received': i.get('amountTo'), 'err': i.get('message') if i.get('error') else None, 'limits_in': lim}
        if i.get('amountTo'):
            r['buy_cost_pct_vs_cg'] = round((1 - i['amountTo'] * mid_cg / usd) * 100, 2)
            r['buy_cost_pct_vs_binance_mid'] = round((1 - i['amountTo'] * mid_bn / usd) * 100, 2)
            back = get(f'https://api.nanswap.com/get-estimate?from=XNO&to={pair}&amount={i["amountTo"]}')
            if back.get('amountTo'):
                r['round_trip_usd_back'] = back['amountTo']; r['round_trip_loss_pct'] = round((1 - back['amountTo'] / usd) * 100, 2)
            else: r['round_trip_err'] = back.get('message')
        rows.append(r)
ex = []
for usd in (1, 10, 100, 1000):
    x = book_buy(usd)
    ex.append({'usd': usd, 'xno_bought_book_only': x, 'slippage_pct_vs_mid': None if x is None else round((1 - x * mid_bn / usd) * 100, 3),
               'binance_taker_fee_pct_vip0': 0.1, 'all_in_pct_excl_withdrawal': None if x is None else round((1 - x * 0.999 * mid_bn / usd) * 100, 3)})
out = {'measured_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'), 'mid_coingecko': mid_cg, 'binance_best_bid_ask': [bid0, ask0], 'binance_mid': mid_bn, 'nanswap': rows, 'binance_book_buy': ex,
       'sources': ['https://api.coingecko.com/api/v3/simple/price?ids=nano&vs_currencies=usd', 'https://api.nanswap.com/get-estimate', 'https://api.binance.com/api/v3/depth?symbol=XNOUSDT&limit=1000']}
json.dump(out, open(sys.argv[1], 'w'), indent=1)
print(json.dumps(out, indent=1)[:3500])
