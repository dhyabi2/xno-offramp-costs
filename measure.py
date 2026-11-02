#!/usr/bin/env python3
"""Measure Nanswap public quotes XNO<->USDC(Base) at several sizes and compare to a CoinGecko mid. Read-only GETs; no swap is created."""
import json, urllib.request, datetime, sys
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'xno-offramp-costs/0.1'}), timeout=20))
mid = get('https://api.coingecko.com/api/v3/simple/price?ids=nano&vs_currencies=usd')['nano']['usd']
rows = []
for pair in ('USDC-BASE', 'USDT-BSC', 'USDC-SOL'):
    lim_out = get(f'https://api.nanswap.com/get-limits?from=XNO&to={pair}'); lim_in = get(f'https://api.nanswap.com/get-limits?from={pair}&to=XNO')
    for usd in (1, 5, 25, 100, 250):
        xno = round(usd / mid, 4)
        o = get(f'https://api.nanswap.com/get-estimate?from=XNO&to={pair}&amount={xno}')
        i = get(f'https://api.nanswap.com/get-estimate?from={pair}&to=XNO&amount={usd}')
        r = {'pair': pair, 'size_usd_at_mid': usd}
        r['out_xno_in'] = xno; r['out_received_usd'] = o.get('amountTo'); r['out_err'] = o.get('message') if o.get('error') else None
        if o.get('amountTo'): r['out_cost_pct'] = round((1 - o['amountTo'] / usd) * 100, 2); r['out_cost_usd'] = round(usd - o['amountTo'], 4)
        r['in_usd_in'] = usd; r['in_xno_received'] = i.get('amountTo'); r['in_err'] = i.get('message') if i.get('error') else None
        if i.get('amountTo'): r['in_cost_pct'] = round((1 - i['amountTo'] * mid / usd) * 100, 2)
        r['limits_out_xno'] = lim_out; r['limits_in_usd'] = lim_in
        rows.append(r)
json.dump({'measured_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'), 'mid_price_usd_coingecko': mid, 'source_mid': 'https://api.coingecko.com/api/v3/simple/price?ids=nano&vs_currencies=usd', 'source_quotes': 'https://api.nanswap.com/get-estimate (public, unauthenticated)', 'rows': rows}, open(sys.argv[1], 'w'), indent=1)
for r in rows: print(r['pair'], r['size_usd_at_mid'], r.get('out_cost_pct'), r.get('in_cost_pct'), r['out_err'], r['in_err'])
