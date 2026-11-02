#!/usr/bin/env python3
"""Cost of getting onto XNO at 1 / 5 / 25 / 100 USDC from every route that answers a public read today.
Read-only GETs; no swap is created, no account used, nothing is signed.
    python3 quote_sizes.py data/quote-sizes-$(date -u +%F).json
Routes: Nanswap instant swap (USDC-BASE, USDT-BSC, USDC-SOL), Binance and KuCoin spot books (slippage + published taker fee).
Other services were tried and are recorded in `not_available` with the reason they gave."""
import datetime, json, sys, urllib.request

UA = {"User-Agent": "xno-offramp-costs/0.3"}
SIZES = (1, 5, 25, 100)


def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25))


def try_get(u):
    try:
        return get(u), None
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {str(e)[:80]}"


def walk_asks(asks, usd):
    left, got = usd, 0.0
    for p, q in asks:
        p, q = float(p), float(q)
        take = min(left, p * q)
        got += take / p
        left -= take
        if left <= 1e-9:
            return got
    return None


def main(out):
    cg = get("https://api.coingecko.com/api/v3/simple/price?ids=nano&vs_currencies=usd")["nano"]["usd"]
    bn = get("https://api.binance.com/api/v3/depth?symbol=XNOUSDT&limit=1000")
    kc = get("https://api.kucoin.com/api/v1/market/orderbook/level2_100?symbol=XNO-USDT")["data"]
    mid = lambda b: (float(b["bids"][0][0]) + float(b["asks"][0][0])) / 2  # noqa: E731
    bn_mid, kc_mid = mid(bn), mid(kc)
    res = {"measured_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
           "coingecko_xno_usd": cg, "binance_mid": bn_mid, "kucoin_mid": kc_mid, "swap": [], "book": [], "not_available": []}
    for pair in ("USDC-BASE", "USDT-BSC", "USDC-SOL"):
        lim, err = try_get(f"https://api.nanswap.com/get-limits?from={pair}&to=XNO")
        for usd in SIZES:
            q, err = try_get(f"https://api.nanswap.com/get-estimate?from={pair}&to=XNO&amount={usd}")
            row = {"route": f"Nanswap {pair}->XNO", "usd_in": usd, "limits": lim}
            if q and q.get("amountTo"):
                x = q["amountTo"]
                row.update(xno=x, cost_pct_vs_coingecko=round((1 - x * cg / usd) * 100, 2),
                           cost_pct_vs_binance_mid=round((1 - x * bn_mid / usd) * 100, 2))
            else:
                row["error"] = err or str(q)[:100]
            res["swap"].append(row)
    for name, book, m, fee in (("Binance XNO/USDT", bn, bn_mid, 0.1), ("KuCoin XNO/USDT", kc, kc_mid, None)):
        for usd in SIZES:
            x = walk_asks(book["asks"], usd)
            row = {"route": name, "usd_in": usd, "needs_account": True}
            if x is None:
                row["error"] = "book too shallow in the snapshot"
            else:
                row.update(xno_before_fee=x, slippage_pct_vs_mid=round((1 - x * m / usd) * 100, 3), taker_fee_pct=fee,
                           all_in_pct_excl_deposit_and_withdrawal=None if fee is None else round((1 - x * (1 - fee / 100) * m / usd) * 100, 3))
            res["book"].append(row)
    for label, u in (("SideShift", "https://sideshift.ai/api/v2/pair/usdc-base/xno"),
                     ("ChangeNOW", "https://api.changenow.io/v1/exchange-amount/25/usdcbase_xno"),
                     ("SimpleSwap", "https://api.simpleswap.io/v1/get_estimated?fixed=false&currency_from=usdcbase&currency_to=xno&amount=25"),
                     ("Exolix", "https://api.exolix.com/api/v2/rate?coinFrom=USDC&networkFrom=BASE&coinTo=XNO&networkTo=XNO&amount=25&rateType=float"),
                     ("Gate", "https://api.gateio.ws/api/v4/spot/order_book?currency_pair=XNO_USDT"),
                     ("Kraken", "https://api.kraken.com/0/public/Depth?pair=XNOUSD")):
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20).read().decode()[:160]
        except Exception as e:  # noqa: BLE001
            r = f"{type(e).__name__}: {e}"[:160]
        res["not_available"].append({"service": label, "url": u, "answer": r.replace("\n", " ")[:160]})
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({"measured_at": res["measured_at"], "cg": cg, "bn_mid": bn_mid, "kc_mid": kc_mid}))
    for r in res["swap"]:
        print(r["route"], r["usd_in"], r.get("cost_pct_vs_coingecko"), r.get("error", ""))


if __name__ == "__main__":
    main(sys.argv[1])
