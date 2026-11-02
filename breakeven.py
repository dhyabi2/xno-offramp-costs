#!/usr/bin/env python3
"""Break-even: what one paid call costs on Base USDC (gas) against XNO (swap in, then feeless calls).

Computes and, with --measure, reads three public GET/RPC surfaces; it holds no key and moves no money.

  python3 breakeven.py --price-usd 0.01 --calls 5000 [--gas-usd G | --measure] [--cash-out-pct X] [--json]

Model (every number is an input or a dated measurement, nothing assumed):
  base_per_call = gas_usd                        flat per payment, whatever the price (payer-side or facilitator-side)
  xno_per_call  = price * spread(F)/100 + gas/N  F = price * calls = the float swapped once; spread(F) is interpolated
                                                 (log size) from data/onramp-2026-11-02.json, Nanswap USDC-BASE -> XNO,
                                                 vs CoinGecko mid; the gas/N term is the one Base transfer that funds the swap
  cash-out      --cash-out-pct adds a seller-side cost on the XNO route (default 0 = seller keeps/spends XNO)
Because gas is flat and the spread is a share, XNO is cheaper per call only BELOW break_even_price = gas/spread.
Above it the flat gas is the smaller number. The tool prints which side you are on.
"""
import argparse
import json
import math
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "onramp-2026-11-02.json")
USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
# transfer(), transferWithAuthorization(v,r,s) and (bytes signature): the calls a payment actually makes
SELECTORS = {"a9059cbb", "e3ee160e", "cf092995"}
NODE = "https://base-rpc.publicnode.com"


def curve(path=DATA):
    d = json.load(open(path))
    pts = sorted((r["usd_in"], r["buy_cost_pct_vs_cg"]) for r in d["nanswap"] if r["pair"] == "USDC-BASE" and not r.get("err"))
    return pts, d["measured_at"], d["nanswap"][0]["limits_in"]


def spread_pct(F, pts):
    if F <= pts[0][0]:
        return pts[0][1]
    if F >= pts[-1][0]:
        return pts[-1][1]
    for (a, ca), (b, cb) in zip(pts, pts[1:]):
        if a <= F <= b:
            t = (math.log(F) - math.log(a)) / (math.log(b) - math.log(a))
            return ca + t * (cb - ca)


def per_call(price, calls, gas, pts, cash_out_pct=0.0):
    if price <= 0 or calls < 1 or gas < 0:
        raise ValueError("price > 0, calls >= 1, gas >= 0")
    F = price * calls
    s = spread_pct(F, pts)
    xno = price * (s + cash_out_pct) / 100 + gas / calls
    return {"float_usd": F, "spread_pct": round(s, 4), "base_usd_per_call": gas, "xno_usd_per_call": xno,
            "base_share_of_price_pct": 100 * gas / price, "xno_share_of_price_pct": 100 * xno / price,
            "cheaper": "xno" if xno < gas else "base"}


def break_even_price(calls, gas, pts, cash_out_pct=0.0):
    """Largest price at which XNO is still cheaper per call, by bisection; None if XNO is never cheaper."""
    lo, hi = 1e-6, 1e5
    f = lambda p: per_call(p, calls, gas, pts, cash_out_pct)["xno_usd_per_call"] - gas
    if f(lo) >= 0:
        return None
    if f(hi) < 0:
        return hi
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
    return lo


def _rpc(method, params):
    r = urllib.request.Request(NODE, json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
                               {"content-type": "application/json", "user-agent": "Mozilla/5.0"})
    return json.load(urllib.request.urlopen(r, timeout=30))["result"]


def measure_gas(n=15):
    """Median cost in USD of recent plain USDC transfers on Base: gas*price + l1Fee, at Coinbase's ETH spot."""
    bn = int(_rpc("eth_blockNumber", []), 16)
    logs = _rpc("eth_getLogs", [{"fromBlock": hex(bn - 40), "toBlock": hex(bn), "address": USDC, "topics": [TRANSFER]}])
    seen, costs = set(), []
    for lg in logs:
        h = lg["transactionHash"]
        if h in seen:
            continue
        seen.add(h)
        tx = _rpc("eth_getTransactionByHash", [h])
        if not tx or (tx.get("to") or "").lower() != USDC.lower() or tx["input"][2:10] not in SELECTORS:
            continue
        rc = _rpc("eth_getTransactionReceipt", [h])
        wei = int(rc["gasUsed"], 16) * int(rc["effectiveGasPrice"], 16) + int(rc.get("l1Fee", "0x0"), 16)
        costs.append(wei)
        if len(costs) >= n:
            break
    if len(costs) < 5:
        raise RuntimeError(f"only {len(costs)} plain USDC transfers found in the last 40 blocks; no number printed")
    eth = float(json.load(urllib.request.urlopen(urllib.request.Request(
        "https://api.coinbase.com/v2/prices/ETH-USD/spot", headers={"user-agent": "Mozilla/5.0"}), timeout=30))["data"]["amount"])
    costs.sort()
    med = costs[len(costs) // 2]
    return {"gas_usd": med / 1e18 * eth, "samples": len(costs), "min_usd": costs[0] / 1e18 * eth,
            "max_usd": costs[-1] / 1e18 * eth, "eth_usd": eth, "block": bn,
            "read_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "method": f"median of {len(costs)} recent USDC transfer/transferWithAuthorization txs on Base: gasUsed*effectiveGasPrice + l1Fee, ETH at Coinbase spot"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--price-usd", type=float, required=True)
    ap.add_argument("--calls", type=int, required=True, help="calls paid out of one XNO float")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--gas-usd", type=float)
    g.add_argument("--measure", action="store_true")
    ap.add_argument("--cash-out-pct", type=float, default=0.0)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    pts, at, lim = curve()
    m = measure_gas() if a.measure else None
    gas = m["gas_usd"] if m else a.gas_usd
    r = per_call(a.price_usd, a.calls, gas, pts, a.cash_out_pct)
    r["break_even_price_usd"] = break_even_price(a.calls, gas, pts, a.cash_out_pct)
    r["spread_measured_at"] = at
    r["swap_min_usd"] = lim["min"]
    r["gas_source"] = m or "given by --gas-usd"
    notes = []
    if r["float_usd"] < lim["min"]:
        notes.append("float below the swap minimum: that float cannot be swapped at all")
    if r["float_usd"] < pts[0][0]:
        notes.append("float below the smallest measured swap ($%g): its spread is used as given, real small swaps cost more" % pts[0][0])
    notes.append("excludes the seller's own cash-out (use --cash-out-pct), the buyer's time, and any facilitator fee")
    r["notes"] = notes
    if a.json:
        print(json.dumps(r, indent=1))
    else:
        be = r["break_even_price_usd"]
        print(f"price ${a.price_usd:g} x {a.calls} calls (float ${r['float_usd']:g}, swap spread {r['spread_pct']}%)")
        print(f"  Base USDC : ${gas:.6f} gas per call = {r['base_share_of_price_pct']:.2f}% of the price")
        print(f"  XNO       : ${r['xno_usd_per_call']:.6f} per call = {r['xno_share_of_price_pct']:.2f}% of the price")
        print(f"  cheaper   : {r['cheaper']}; XNO is cheaper below a price of about " + (f"${be:.4f}" if be else "none (never)") + " for this float size")
        for n in notes:
            print("  note:", n)
    return r


if __name__ == "__main__":
    main()
