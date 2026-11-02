#!/usr/bin/env python3
"""Sell-side curve: XNO -> USDC-BASE at 10/50/250/1000 XNO plus buys at 1/5/25 USDC, quotes taken back to back against ONE mid read. Read-only GETs.
Usage: python3 sellcurve.py out.json"""
import json, urllib.request, datetime, sys
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'xno-offramp-costs/0.2'}), timeout=25))
now = lambda: datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
mid_t = now(); mid = get('https://api.coingecko.com/api/v3/simple/price?ids=nano&vs_currencies=usd')['nano']['usd']
rows = []
for x in (10, 50, 250, 1000):
    q = get(f'https://api.nanswap.com/get-estimate?from=XNO&to=USDC-BASE&amount={x}')
    rows.append({'side': 'sell', 'xno': x, 'usdc_out': q.get('amountTo'), 'kept_of_mid_pct': round(q['amountTo'] / (x * mid) * 100, 2) if q.get('amountTo') else None, 'err': q.get('message') if q.get('error') else None, 'at': now()})
for u in (1, 5, 25):
    q = get(f'https://api.nanswap.com/get-estimate?from=USDC-BASE&to=XNO&amount={u}')
    rows.append({'side': 'buy', 'usdc': u, 'xno_out': q.get('amountTo'), 'kept_of_mid_pct': round(q['amountTo'] * mid / u * 100, 2) if q.get('amountTo') else None, 'err': q.get('message') if q.get('error') else None, 'at': now()})
json.dump({'mid_usd': mid, 'mid_read_at': mid_t, 'mid_source': 'https://api.coingecko.com/api/v3/simple/price?ids=nano&vs_currencies=usd', 'rows': rows}, open(sys.argv[1], 'w'), indent=1)
for r in rows: print(r)
