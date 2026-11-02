import unittest

import swap_receipt as sr

BLK = "B749B757EE750FC9AEA72F33CB429EACCD2ABEC9F2CCF59BF17AFAC304C9A58F"
TX = "0x" + "ab" * 32
ME = "0x" + "11" * 20


def fake(nano=None, base=None):
    def post(url, body, timeout=20):
        if body.get("action") == "block_info":
            if isinstance(nano, Exception):
                raise nano
            return nano
        return base
    return post


NANO = {"confirmed": "true", "subtype": "send", "amount": "500000000000000000000000000", "block_account": "nano_a",
        "contents": {"link_as_account": "nano_b"}}


def base(amount=4_500_000, to=ME, status="0x1"):
    return {"result": {"status": status, "blockNumber": "0x10", "logs": [
        {"address": sr.USDC_BASE, "topics": [sr.TRANSFER, "0x" + "0" * 64, "0x" + "0" * 24 + to[2:]], "data": hex(amount)}]}}


class T(unittest.TestCase):
    def test_both_legs_verified_and_pairing_is_labelled(self):
        r = sr.receipt(BLK, TX, ME, 4.0, "ord1", fake(NANO, base()))
        self.assertEqual(r["verdict"], "verified")
        self.assertEqual(r["usdc_leg"]["usdc"], 4.5)
        self.assertEqual(r["pairing"], "asserted, not on-chain")

    def test_below_min_is_wrong(self):
        self.assertEqual(sr.receipt(BLK, TX, ME, 5.0, None, fake(NANO, base()))["verdict"], "wrong")

    def test_transfer_to_someone_else_is_wrong(self):
        self.assertEqual(sr.receipt(BLK, TX, ME, None, None, fake(NANO, base(to="0x" + "22" * 20)))["verdict"], "wrong")

    def test_reverted_is_wrong(self):
        self.assertEqual(sr.receipt(BLK, TX, ME, None, None, fake(NANO, base(status="0x0")))["verdict"], "wrong")

    def test_unreadable_is_unknown_not_wrong(self):
        self.assertEqual(sr.receipt(BLK, TX, ME, None, None, fake(OSError(), base()))["verdict"], "unknown")
        self.assertEqual(sr.receipt(BLK, TX, ME, None, None, fake(NANO, {"result": None}))["verdict"], "unknown")

    def test_unconfirmed_or_not_send_is_wrong(self):
        self.assertEqual(sr.receipt(BLK, TX, ME, None, None, fake(dict(NANO, confirmed="false"), base()))["verdict"], "wrong")

    def test_malformed_inputs_refused(self):
        self.assertEqual(sr.receipt("xx", TX, ME, None, None, fake(NANO, base()))["verdict"], "wrong")

    def test_other_token_log_not_counted(self):
        b = base()
        b["result"]["logs"][0]["address"] = "0x" + "99" * 20
        self.assertEqual(sr.receipt(BLK, TX, ME, None, None, fake(NANO, b))["verdict"], "wrong")


class Order(unittest.TestCase):
    ORDER = {"id": "o1", "from": "usdc", "fromNetwork": "base", "to": "XNO", "status": "completed", "amountFrom": 2.5,
             "amountTo": 6.2, "payinHash": TX, "payoutHash": BLK, "payinAddress": ME, "payoutAddress": "nano_b"}

    def run_order(self, order, nano=NANO, b=None):
        return sr.receipt_from_order("o1", fake(nano, b or base(amount=2_500_000, to=ME)), get=lambda u: order)

    def test_usdc_to_xno_order_verifies_both_legs(self):
        r = self.run_order(self.ORDER)
        self.assertEqual((r["verdict"], r["direction"]), ("verified", "usdc->xno"))

    def test_quote_vs_delivered_is_reported(self):
        r = self.run_order(dict(self.ORDER, expectedAmountTo=7.0, amountTo=6.3))
        self.assertAlmostEqual(r["quote_vs_delivered_pct"], -10.0, places=3)
        self.assertIsNone(self.run_order(self.ORDER)["quote_vs_delivered_pct"])        # no expected amount on the order: not guessed

    def test_order_not_completed_is_unknown(self):
        self.assertEqual(self.run_order(dict(self.ORDER, status="waiting"))["verdict"], "unknown")
        self.assertEqual(self.run_order({"error": "Transaction doesn't exist"})["verdict"], "unknown")

    def test_usdc_below_order_amount_is_wrong(self):
        self.assertEqual(self.run_order(self.ORDER, b=base(amount=1_000_000, to=ME))["verdict"], "wrong")

    def test_xno_paid_to_a_different_account_than_the_order_says_is_wrong(self):
        nano = dict(NANO, contents={"link_as_account": "nano_other"})
        self.assertEqual(self.run_order(self.ORDER, nano=nano)["verdict"], "wrong")

    def test_xno_to_usdc_direction_swaps_roles(self):
        o = dict(self.ORDER, **{"from": "XNO", "to": "usdc", "payinHash": BLK, "payoutHash": TX, "payoutAddress": ME,
                                "amountTo": 2.5})
        r = self.run_order(o)
        self.assertEqual((r["verdict"], r["direction"]), ("verified", "xno->usdc"))


if __name__ == "__main__":
    unittest.main()
