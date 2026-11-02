#!/usr/bin/env python3
"""Second-provider swap/quote comparison for USDC -> XNO at 1/25/100 USD, plus the round trip. Read-only public GETs, nothing is swapped.
Providers: Nanswap instant swap (USDC-BASE), and four public order books (Binance, KuCoin, Kraken, Gate) walked for a market buy and a market sell.
Usage: python3 compare_providers.py [out.json]   -> writes JSON and prints a markdown table."""
import json, sys, datetime, urllib.request
SIZES = (1, 25, 100)
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'xno-offramp-costs/0.3'}), timeout=25))
def books():
    b = get('https://api.binance.com/api/v3/depth?symbol=XNOUSDT&limit=1000')
    k = get('https://api.kucoin.com/api/v1/market/orderbook/level2_100?symbol=XNO-USDT')['data']
    r = get('https://api.kraken.com/0/public/Depth?pair=NANOUSD&count=500')['result']['NANOUSD']
    g = get('https://api.gateio.ws/api/v4/spot/order_book?currency_pair=NANO_USDT&limit=100')
    f = lambda x: {'asks': [(float(p), float(q)) for p, q, *_ in x['asks']], 'bids': [(float(p), float(q)) for p, q, *_ in x['bids']]}
    return {'Binance XNO/USDT': f(b), 'KuCoin XNO/USDT': f(k), 'Kraken NANO/USD': f(r), 'Gate NANO/USDT': f(g)}
def buy(book, usd):
    left, got = usd, 0.0
    for p, q in sorted(book['asks']):
        t = min(left, p * q); got += t / p; left -= t
        if left <= 1e-9: return got
def sell(book, xno):
    left, got = xno, 0.0
    for p, q in sorted(book['bids'], reverse=True):
        t = min(left, q); got += t * p; left -= t
        if left <= 1e-9: return got
def main():
    cg = get('https://api.coingecko.com/api/v3/simple/price?ids=nano&vs_currencies=usd')['nano']['usd']
    out = {'measured_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'), 'coingecko_usd': cg, 'rows': []}
    for usd in SIZES:
        i = get(f'https://api.nanswap.com/get-estimate?from=USDC-BASE&to=XNO&amount={usd}')
        x = i.get('amountTo'); row = {'provider': 'Nanswap swap (USDC-BASE)', 'usd': usd, 'xno': x}
        if x:
            back = get(f'https://api.nanswap.com/get-estimate?from=XNO&to=USDC-BASE&amount={x}').get('amountTo')
            row.update(buy_cost_pct=round((1 - x * cg / usd) * 100, 2), round_trip_loss_pct=round((1 - back / usd) * 100, 2) if back else None)
        out['rows'].append(row)
    for name, bk in books().items():
        for usd in SIZES:
            x = buy(bk, usd); back = sell(bk, x) if x else None
            out['rows'].append({'provider': name + ' book', 'usd': usd, 'xno': x,
                'buy_cost_pct': None if not x else round((1 - x * cg / usd) * 100, 2),
                'round_trip_loss_pct': None if not back else round((1 - back / usd) * 100, 2)})
    return out
if __name__ == '__main__':
    o = main()
    if len(sys.argv) > 1: json.dump(o, open(sys.argv[1], 'w'), indent=1)
    print('| Provider | USD in | XNO out | Cost vs CoinGecko | Round trip loss (no fees) |\n|---|---|---|---|---|')
    for r in o['rows']:
        f = lambda v: 'n/a' if v is None else f'{v}%'
        print(f"| {r['provider']} | {r['usd']} | {'n/a' if not r['xno'] else round(r['xno'], 4)} | {f(r.get('buy_cost_pct'))} | {f(r.get('round_trip_loss_pct'))} |")
