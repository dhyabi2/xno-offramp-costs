#!/usr/bin/env python3
"""swap_receipt: pair an XNO send block with a USDC-on-Base transfer into one receipt. Read-only.

    python3 swap_receipt.py --xno-block HASH --usdc-tx 0x.. --payout-address 0x.. [--min-usdc 4.5] [--order-id ID]

It never swaps, signs or sends. It asks one Nano node for block_info and one Base node for the transaction
receipt, checks each leg on its own, and prints JSON. WHAT IT PROVES: leg A (XNO left the sender's account in a
confirmed send block of N raw) and leg B (a USDC Transfer of M units to your address is in a successful Base
transaction). WHAT IT CANNOT PROVE: that leg A caused leg B. A swap service sits in between and holds the funds
in transit; the pairing comes from the service's order record, which the receipt carries as `claimed_by_order`
and marks `pairing: "asserted, not on-chain"`. Exit 0 both legs verified, 2 a leg could not be read, 4 a leg is wrong.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request

NANO_RPC = "https://rpc.nano.to"
BASE_RPC = "https://mainnet.base.org"
USDC_BASE = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
UA = "Mozilla/5.0 (xno-offramp-costs swap_receipt)"


def post(url, body, timeout=20):
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def leg_xno(block, post=post, rpc=NANO_RPC):
    if not re.fullmatch(r"[0-9A-Fa-f]{64}", block):
        return {"ok": False, "state": "refused", "why": "xno block is not 64 hex"}
    try:
        d = post(rpc, {"action": "block_info", "json_block": "true", "hash": block.upper()})
    except Exception as e:
        return {"ok": None, "state": "unreadable", "why": f"{type(e).__name__}"}
    if not isinstance(d, dict) or "error" in d:
        return {"ok": None, "state": "unreadable", "why": str((d or {}).get("error", "bad reply"))[:80]}
    sub = (d.get("subtype") or d.get("contents", {}).get("subtype"))
    ok = d.get("confirmed") in ("true", True) and sub == "send"
    return {"ok": ok, "state": "verified" if ok else "wrong", "node": rpc, "block_hash": block.upper(),
            "subtype": sub, "confirmed": d.get("confirmed"), "amount_raw": d.get("amount"),
            "source": d.get("block_account"), "destination": d.get("contents", {}).get("link_as_account")}


def leg_usdc(tx, payout, min_usdc=None, post=post, rpc=BASE_RPC):
    if not re.fullmatch(r"0x[0-9a-fA-F]{64}", tx) or not re.fullmatch(r"0x[0-9a-fA-F]{40}", payout):
        return {"ok": False, "state": "refused", "why": "tx or payout address malformed"}
    try:
        d = post(rpc, {"jsonrpc": "2.0", "id": 1, "method": "eth_getTransactionReceipt", "params": [tx]})
    except Exception as e:
        return {"ok": None, "state": "unreadable", "why": f"{type(e).__name__}"}
    r = d.get("result") if isinstance(d, dict) else None
    if not r:
        return {"ok": None, "state": "unreadable", "why": "no receipt (unknown tx, pending, or node error)"}
    if r.get("status") != "0x1":
        return {"ok": False, "state": "wrong", "why": "transaction reverted", "tx": tx}
    want = "0x" + "0" * 24 + payout[2:].lower()
    total = 0
    for lg in r.get("logs", []):
        t = lg.get("topics", [])
        if lg.get("address", "").lower() == USDC_BASE and len(t) == 3 and t[0] == TRANSFER and t[2].lower() == want:
            total += int(lg["data"], 16)
    usdc = total / 10 ** 6  # USDC has 6 decimals
    ok = total > 0 and (min_usdc is None or usdc >= min_usdc)
    return {"ok": ok, "state": "verified" if ok else "wrong", "node": rpc, "tx": tx, "token_contract": USDC_BASE,
            "to": payout.lower(), "usdc_units": str(total), "usdc": usdc, "block_number": int(r["blockNumber"], 16),
            "why": None if ok else "no USDC Transfer to the payout address in this tx (or below --min-usdc)"}


def receipt(xno_block, usdc_tx, payout, min_usdc=None, order_id=None, post=post):
    a, b = leg_xno(xno_block, post), leg_usdc(usdc_tx, payout, min_usdc, post)
    legs = (a["ok"], b["ok"])
    verdict = "verified" if legs == (True, True) else "wrong" if False in legs else "unknown"
    return {"v": "xno-usdc-swap-receipt-v1", "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "verdict": verdict, "xno_leg": a, "usdc_leg": b,
            "pairing": "asserted, not on-chain",
            "claimed_by_order": {"order_id": order_id, "note": "the swap service's own record; a custodian sits between the legs"}
            if order_id else None}


def main(argv=None, post=post):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--xno-block", required=True)
    p.add_argument("--usdc-tx", required=True)
    p.add_argument("--payout-address", required=True)
    p.add_argument("--min-usdc", type=float)
    p.add_argument("--order-id")
    a = p.parse_args(argv)
    r = receipt(a.xno_block, a.usdc_tx, a.payout_address, a.min_usdc, a.order_id, post)
    print(json.dumps(r, indent=2))
    return {"verified": 0, "unknown": 2, "wrong": 4}[r["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
