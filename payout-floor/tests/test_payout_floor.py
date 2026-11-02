import json, os, re, sys
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import payout_floor as pf

X = pf.XNO
NOW = "2026-11-02T08:00:00Z"
OBS = pf.validate_observations([
    {"id": "a", "pair": "XNO->USDC", "size_raw": str(3 * X), "received_raw": str(687714), "mid_raw": "325352",
     "observed_at": "2026-11-02T06:10:00Z", "source": "t"},
    {"id": "b", "pair": "XNO->USDC", "size_raw": str(300 * X), "received_raw": str(95639992), "mid_raw": "325352",
     "observed_at": "2026-11-02T06:10:00Z", "source": "t"}])
FLOOR = X * 3 // 100 * 0 + int(0.03 * 1000) * X // 1000  # 0.03 XNO as an integer


def test_floor_binds_means_zero_kept():
    e = pf.estimate(FLOOR // 2, {"kind": "offramp_each", "min_credit_raw": FLOOR}, observations=OBS, now=NOW)
    assert e["floor_binds"] is True and e["keeps_raw"] == "0"


def test_spend_direct_keeps_all():
    e = pf.estimate(FLOOR // 2, {"kind": "spend_direct"}, observations=OBS, now=NOW)
    assert e["floor_binds"] is False and e["keeps_raw"] == str(FLOOR // 2)


def test_compare_ranks_direct_first_offramp_last():
    p = FLOOR // 2
    r = pf.compare(p, [{"kind": "offramp_each", "min_credit_raw": FLOOR}, {"kind": "spend_direct"},
                       {"kind": "batch_then_offramp", "min_credit_raw": FLOOR, "batch_n": 50}], observations=OBS, now=NOW)
    assert r[0]["route"] == "spend_direct" and r[-1]["route"] == "offramp_each"


def test_batch_keeps_more_than_each():
    p = FLOOR // 2
    each = pf.estimate(p, {"kind": "offramp_each", "min_credit_raw": FLOOR}, observations=OBS, now=NOW)
    bat = pf.estimate(p, {"kind": "batch_then_offramp", "min_credit_raw": FLOOR, "batch_n": 20}, observations=OBS, now=NOW)
    assert int(bat["keeps_raw"]) > int(each["keeps_raw"])


def test_no_hardcoded_rate_in_source():
    src = open(pf.__file__).read()
    assert not re.search(r"(?<![\w.])0?\.(?:[5-9]\d*)\b", src.replace("0.0", "")), "a rate literal appears in the source"


def test_empty_observations_gives_null_and_unknown():
    for k in pf.KINDS[1:]:
        e = pf.estimate(X, {"kind": k, "min_credit_raw": 1, "batch_n": 2, "spread_observations": []}, observations={}, now=NOW)
        assert e["keeps_raw"] is None and e["unknown"]


def test_floats_refused():
    with pytest.raises(ValueError):
        pf.estimate(0.05 * 10 ** 30, {"kind": "spend_direct"}, observations=OBS)
    assert int(0.05 * 10 ** 30) != 50 * 10 ** 27
    with pytest.raises(ValueError):
        pf.estimate(1, {"kind": "offramp_each", "min_credit_raw": 1.5}, observations=OBS)


def test_bad_kind_names_the_three():
    with pytest.raises(ValueError) as e:
        pf.estimate(1, {"kind": "x"}, observations=OBS)
    assert all(k in str(e.value) for k in pf.KINDS)


def test_unknown_observation_id():
    with pytest.raises(ValueError, match="nope"):
        pf.estimate(X, {"kind": "offramp_each", "spread_observations": ["nope"]}, observations=OBS)


def test_stale_observation_is_flagged_but_used():
    e = pf.estimate(X, {"kind": "offramp_each", "min_credit_raw": 1}, observations=OBS, now="2026-11-04T00:00:00Z")
    assert e["keeps_raw"] is not None and any("stale" in u for u in e["unknown"])


def test_min_credit_none_gives_floor_unknown():
    e = pf.estimate(X, {"kind": "offramp_each"}, observations=OBS, now=NOW)
    assert e["floor_binds"] is None


def test_json_roundtrip_and_string_fraction():
    e = pf.estimate(X, {"kind": "offramp_each", "min_credit_raw": 1}, observations=OBS, now=NOW)
    assert isinstance(e["keeps_fraction"], str) and json.loads(json.dumps(e)) == e


def test_free_lunch_rejected():
    with pytest.raises(ValueError, match="x1"):
        pf.validate_observations([{"id": "x1", "size_raw": str(X), "received_raw": "999999999", "mid_raw": "325352",
                                   "observed_at": "2026-11-02T06:10:00Z"}])


def test_unknown_names_the_edges():
    e = pf.estimate(X, {"kind": "offramp_each", "min_credit_raw": 1}, observations=OBS, now=NOW)
    assert any("fees" in u for u in e["unknown"]) and any("bridge" in u for u in e["unknown"]) and any("price movement" in u for u in e["unknown"])


def test_batch_size_unreachable_returns_none():
    assert pf.batch_size(0.999999, {"min_credit_raw": 1}, X, observations=OBS, now=NOW, max_n=5) is None


def test_shipped_observations_load():
    obs = pf.load_observations()
    assert len(obs) == 5


def test_no_network_in_import_graph():
    src = open(pf.__file__).read()
    assert not re.search(r"^\s*(import|from)\s+(urllib|socket|http|requests)", src, re.M)
