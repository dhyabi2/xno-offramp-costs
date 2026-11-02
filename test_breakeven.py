import json, subprocess, sys, unittest
import breakeven as b

PTS, _, LIM = b.curve()


class Breakeven(unittest.TestCase):
    def test_curve_is_the_measured_table(self):
        self.assertEqual([p[0] for p in PTS], [1, 10, 100, 1000])
        self.assertEqual(b.spread_pct(10, PTS), 1.78)
        self.assertEqual(b.spread_pct(0.01, PTS), PTS[0][1])      # clamped, flagged in notes
        self.assertEqual(b.spread_pct(1e6, PTS), PTS[-1][1])
        self.assertTrue(PTS[1][1] > b.spread_pct(30, PTS) > PTS[2][1])

    def test_gas_is_flat_xno_is_a_share(self):
        a = b.per_call(0.01, 1000, 0.002, PTS)
        c = b.per_call(10, 1000, 0.002, PTS)
        self.assertEqual(a["base_usd_per_call"], c["base_usd_per_call"])
        self.assertEqual((a["cheaper"], c["cheaper"]), ("xno", "base"))

    def test_break_even_is_where_costs_cross(self):
        be = b.break_even_price(5000, 0.002, PTS)
        lo = b.per_call(be * 0.99, 5000, 0.002, PTS)
        hi = b.per_call(be * 1.01, 5000, 0.002, PTS)
        self.assertEqual((lo["cheaper"], hi["cheaper"]), ("xno", "base"))

    def test_free_gas_means_xno_is_never_cheaper(self):
        self.assertIsNone(b.break_even_price(1000, 0.0, PTS))

    def test_cash_out_cost_moves_the_line_down(self):
        self.assertLess(b.break_even_price(1000, 0.002, PTS, 5.0), b.break_even_price(1000, 0.002, PTS, 0.0))

    def test_bad_input_refused(self):
        for args in ((0, 10, 0.1), (1, 0, 0.1), (1, 10, -1)):
            with self.assertRaises(ValueError):
                b.per_call(*args, PTS)

    def test_cli_json(self):
        out = subprocess.run([sys.executable, "breakeven.py", "--price-usd", "0.03", "--calls", "1000", "--gas-usd", "0.0005", "--json"],
                             capture_output=True, text=True, check=True).stdout
        r = json.loads(out)
        self.assertEqual(r["cheaper"], "xno")
        self.assertIn("excludes", " ".join(r["notes"]))

    def test_gas_snapshot_has_its_method(self):
        m = json.load(open("data/base-gas-2026-11-02.json"))
        self.assertGreaterEqual(m["samples"], 5)
        self.assertIn("l1Fee", m["method"])


if __name__ == "__main__":
    unittest.main()
