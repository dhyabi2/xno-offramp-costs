# XNO to USDC-on-Base: routes and a receipt (read-only, 2026-11-02)

Fees at $1/$5/$25/$100/$250 are in [README.md](README.md) (Nanswap public API, measured today): outbound about
4% plus about $0.30 fixed, so $5 costs 9.6%, $25 costs 5.3%, $100 costs 4.4%. At $3 and $10 interpolate
between the $1 and $5 rows and the $5 and $25 rows; they were not quoted separately.

| Route | XNO to USDC-Base? | Evidence | Account/KYC |
|---|---|---|---|
| Nanswap | yes, `XNO -> USDC-BASE`, min 1.90 XNO | live `get-estimate` / `get-limits`, README sec. 1 | none for quotes; `create-order` needs a free API key (header `nanswap-api-key`, per its Postman docs) |
| Changelly, Xgram | a USDC/XNO page exists on each | search listings only; fees not stated, no quote fetched | not checked |
| Exchange (Binance, KuCoin) then withdraw USDC on Base | XNO/USDT books only; USDC-Base withdrawal fee not verified | README sec. 2 | account and identity checks |

Not found: any trust-minimised bridge from Nano to Base. Nano has no smart contracts, so every route has a
custodian holding value between the two legs.

## The receipt: `swap_receipt.py`

```
python3 swap_receipt.py --order-id <nanswap order id>      # reads the public order, verifies both legs it names
python3 swap_receipt.py --xno-block <64hex> --usdc-tx 0x<64hex> --payout-address 0x<40hex> [--min-usdc 4.5] [--order-id ID]
```

Asks a Nano node for `block_info` (must be a confirmed `send`) and a Base node for the transaction receipt (must
have succeeded and contain a USDC `Transfer` to your address), then prints one JSON receipt. Exit 0 both legs
verified, 2 a leg unreadable, 4 a leg wrong. It never swaps, signs or sends.

Honest limit: the receipt proves two legs separately. That the XNO caused the USDC is the swap service's order
record, so the receipt says `"pairing": "asserted, not on-chain"`.

Run live today, read-only, on a real completed order (the one ARION published: `python3 swap_receipt.py --order-id
00b1d9dfdaac3f`, USDC-Base to XNO, 2026-09-23): both legs verified, exit 0. Base tx 0xa4992fe6... moved 2.5 USDC to the
order's pay-in address, and Nano block DC8D11E6... is a confirmed send of 6.2756 XNO to the order's payout account. Field
names (`payinHash`, `payoutHash`, `payinAddress`, `payoutAddress`, `amountFrom`, `amountTo`) are read from that real order.
The XNO-to-USDC direction (payin is the XNO block) is the same code with the roles swapped and is covered by a mocked test
only; no such order was available and none was created. 13 mocked tests (`python3 -m unittest test_swap_receipt`).
Creating an order or sending funds is owner-only and was not done.
