"""xno-payout-floor: what an agent keeps of an XNO payout once the edges are counted.

Computes only. Reads no price feed, fetches no quote, holds no key, moves no money. Every rate comes from an
Observation (a swap actually measured); there is no rate in this file. Integer raw arithmetic throughout.

Units (fixed, written down so nobody guesses):
  payout_raw, Observation.size_raw : XNO in raw (1 XNO = 10**30)
  Observation.received_raw         : what the off-ramp credited, in millionths of a USD-like unit (10**-6)
  Observation.mid_raw              : the reference mid price, in millionths of that unit per 1 XNO
  min_credit_raw                   : the off-ramp's smallest credited deposit, in XNO raw
  Estimate.keeps_raw               : XNO-raw-equivalent at the observed mid (so routes compare in one unit)
"""
import json
import os
import datetime as dt

XNO = 10 ** 30
KINDS = ("spend_direct", "offramp_each", "batch_then_offramp")
STALE_S = 24 * 3600
ALWAYS_UNKNOWN = [
    "the destination account's own fees",
    "any bridge or custody step after the swap",
    "price movement between the observation and the payout",
]
HERE = os.path.dirname(os.path.abspath(__file__))


def _int(name, v, allow_none=False):
    if v is None and allow_none:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, str)):
        raise ValueError(f"{name} must be an integer (raw), got {type(v).__name__}: a float would truncate silently")
    try:
        return int(v)
    except ValueError:
        raise ValueError(f"{name} must be an integer (raw), got {v!r}")


def _ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def load_observations(path=None):
    path = path or os.path.join(HERE, "observations.json")
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return validate_observations(raw)


def validate_observations(raw):
    out = {}
    for o in raw:
        oid = o.get("id")
        size, rec, mid = (_int(f"{oid}.{k}", o[k]) for k in ("size_raw", "received_raw", "mid_raw"))
        if size <= 0 or rec < 0 or mid <= 0:
            raise ValueError(f"observation {oid}: size and mid must be positive")
        if rec * XNO > size * mid:
            raise ValueError(f"observation {oid}: received more than the mid price allows (a free lunch); refusing it")
        out[oid] = {**o, "size_raw": size, "received_raw": rec, "mid_raw": mid}
    return out


def _frac(num, den):
    q = num * 10 ** 6 // den
    return f"{q // 10**6}.{q % 10**6:06d}"


def _pick(route, observations, total_raw):
    ids = route.get("spread_observations") or list(observations)
    for i in ids:
        if i not in observations:
            raise ValueError(f"unknown observation id {i!r}")
    if not ids:
        return None, []
    best = min(ids, key=lambda i: abs(observations[i]["size_raw"] - total_raw))
    return observations[best], [best]


def estimate(payout_raw, route, *, observations, now=None):
    payout_raw = _int("payout_raw", payout_raw)
    if payout_raw < 0:
        raise ValueError("payout_raw must not be negative")
    kind = route.get("kind")
    if kind not in KINDS:
        raise ValueError(f"route.kind must be one of {', '.join(KINDS)}; got {kind!r}")
    mc = _int("min_credit_raw", route.get("min_credit_raw"), allow_none=True)
    n = 1
    if kind == "batch_then_offramp":
        n = _int("batch_n", route.get("batch_n"))
        if n < 1:
            raise ValueError("batch_n must be at least 1")
    unknown = list(ALWAYS_UNKNOWN)
    if kind == "spend_direct":
        return {"route": kind, "keeps_raw": str(payout_raw), "keeps_fraction": _frac(1, 1),
                "floor_binds": False, "basis": [], "unknown": ["whatever the payee charges for the thing bought"],
                "why": "no conversion, so no off-ramp floor and no spread"}
    total = payout_raw * n
    binds = None if mc is None else total < mc
    if mc is None:
        unknown.append("min_credit_raw not given, so whether a floor binds is unknown")
    if binds:
        return {"route": kind, "keeps_raw": "0", "keeps_fraction": _frac(0, 1), "floor_binds": True, "basis": [],
                "unknown": unknown, "why": f"{total} raw is below the off-ramp's smallest credited deposit {mc} raw: it keeps nothing"}
    ob, basis = _pick(route, observations, total)
    if ob is None:
        unknown.append("no observation of this off-ramp: nothing measured, nothing estimated")
        return {"route": kind, "keeps_raw": None, "keeps_fraction": None, "floor_binds": binds, "basis": [],
                "unknown": unknown, "why": "no Observation supplied"}
    ref = _ts(now) if isinstance(now, str) else (now or dt.datetime.now(dt.timezone.utc))
    if (ref - _ts(ob["observed_at"])).total_seconds() > STALE_S:
        unknown.append(f"stale: observation {ob['id']} is older than 24 h")
    lo = min(o["size_raw"] for o in observations.values())
    hi = max(o["size_raw"] for o in observations.values())
    if not lo <= total <= hi:
        unknown.append("the amount is outside the sizes measured; nearest observation reused, not extrapolated")
    expected = ob["size_raw"] * ob["mid_raw"]  # value at mid, scaled by XNO
    keeps = payout_raw * n * ob["received_raw"] * XNO // expected  # total kept, XNO-raw-equivalent
    if kind == "batch_then_offramp":
        keeps_each = keeps // n
    else:
        keeps_each = keeps
    return {"route": kind, "keeps_raw": str(keeps_each), "keeps_fraction": _frac(ob["received_raw"] * XNO, expected),
            "floor_binds": binds, "basis": basis, "unknown": unknown,
            "why": f"scaled by {ob['id']}: received {ob['received_raw']} of {expected // XNO} at mid"}


def compare(payout_raw, routes, *, observations, now=None):
    ests = [estimate(payout_raw, r, observations=observations, now=now) for r in routes]
    return sorted(ests, key=lambda e: -(int(e["keeps_raw"]) if e["keeps_raw"] is not None else -1))


def batch_size(target_keep_fraction, route, payout_raw, *, observations, now=None, max_n=10000):
    """Smallest batch_n whose per-payment keeps_fraction reaches the target, or None. Never loops past max_n."""
    t = int(round(float(target_keep_fraction) * 10 ** 6))
    for n in range(1, max_n + 1):
        e = estimate(payout_raw, {**route, "kind": "batch_then_offramp", "batch_n": n}, observations=observations, now=now)
        if e["keeps_raw"] is None:
            return None
        if e["floor_binds"]:
            continue
        got = int(e["keeps_raw"]) * 10 ** 6 // payout_raw if payout_raw else 0
        if got >= t:
            return n
    return None


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="what an XNO payout keeps after an off-ramp floor and spread")
    ap.add_argument("--payout-xno", required=True, help="decimal XNO, e.g. 0.03")
    ap.add_argument("--min-credit-xno", help="the off-ramp's smallest credited deposit, decimal XNO")
    ap.add_argument("--batch-n", type=int, default=10)
    ap.add_argument("--observations")
    a = ap.parse_args(argv)
    from decimal import Decimal
    p = int(Decimal(a.payout_xno) * XNO)
    mc = int(Decimal(a.min_credit_xno) * XNO) if a.min_credit_xno else None
    obs = load_observations(a.observations)
    routes = [{"kind": "spend_direct"}, {"kind": "offramp_each", "min_credit_raw": mc},
              {"kind": "batch_then_offramp", "min_credit_raw": mc, "batch_n": a.batch_n}]
    print(json.dumps(compare(p, routes, observations=obs), indent=1))


if __name__ == "__main__":
    main()
