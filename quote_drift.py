#!/usr/bin/env python3
"""quote_drift.py - sample Nanswap's public get-estimate repeatedly and report how far the quote moves (read-only, swaps nothing).

  python3 quote_drift.py --pair USDC-BASE:XNO --amounts 10,100,1000 --every 30 --count 24 --out data/x.jsonl
  python3 quote_drift.py --summarize data/nanswap-quote-drift-2026-11-02.jsonl

It measures how the ESTIMATE moves over minutes. It cannot measure the difference between an estimate and what an order finally
pays, because that needs an order (owner-only here); for that, read a finished public order: `swap_receipt.py --order-id ID`
shows expectedAmountTo against amountTo. Two numbers together answer "firm or indicative".
"""
import argparse
import collections
import json
import time
import urllib.request


def estimate(frm, to, amount):
    u = f"https://api.nanswap.com/v1/get-estimate?from={frm}&to={to}&amount={amount}"
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"user-agent": "Mozilla/5.0"}), timeout=20))["amountTo"]


def summarize(path):
    by = collections.defaultdict(list)
    for line in open(path):
        r = json.loads(line)
        if r.get("xno") is not None:
            by[r["usd"]].append((r["t"], r["xno"]))
    out = {}
    for amt, v in sorted(by.items()):
        xs = [x for _, x in v]
        steps = [abs(b / a - 1) * 100 for a, b in zip(xs, xs[1:]) if a != b]
        out[amt] = {"n": len(xs), "from": v[0][0], "to": v[-1][0], "range_pct": round((max(xs) - min(xs)) / min(xs) * 100, 3),
                    "changes": len(steps), "max_step_pct": round(max(steps), 3) if steps else 0.0,
                    "first_to_last_pct": round((xs[-1] / xs[0] - 1) * 100, 3)}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", default="USDC-BASE:XNO")
    ap.add_argument("--amounts", default="10,100,1000")
    ap.add_argument("--every", type=int, default=30)
    ap.add_argument("--count", type=int, default=24)
    ap.add_argument("--out")
    ap.add_argument("--summarize")
    a = ap.parse_args()
    if a.summarize:
        print(json.dumps(summarize(a.summarize), indent=1))
        return
    frm, to = a.pair.split(":")
    out = open(a.out, "w")
    for i in range(a.count):
        t = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        for amt in a.amounts.split(","):
            try:
                x = estimate(frm, to, amt)
            except Exception:
                x = None
            out.write(json.dumps({"t": t, "usd": float(amt) if "." in amt else int(amt), "xno": x}) + "\n")
        out.flush()
        time.sleep(a.every)


if __name__ == "__main__":
    main()
