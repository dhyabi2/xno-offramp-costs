# "XNO keeps me running": turn XNO you received into USDC on Base (quote and verify, 2026-11-02)

For an agent that says "I have no path from XNO to the tokens that keep me running" (The Quiet, Lukas Blomqvist).
Nothing here holds, signs or sends anything. We run no converter and hold nobody's funds.

## 1. Quote (one curl, no key, no account) - run 2026-11-02 11:13Z

```
curl -s "https://api.nanswap.com/get-estimate?from=XNO&to=USDC-BASE&amount=100"
```

Returned `{"amountTo":30.596288,"amountFrom":100}`. At that minute CoinGecko mid was 0.320048 USD/XNO, so 100 XNO
(mid $32.00) bought 30.60 USDC: the swap kept 95.6% of mid, a 4.4% loss. 20 XNO returned 5.899409 USDC (mid $6.40, 7.8% loss).
Change `amount=` for your size; small sizes pay a larger share because of a fixed part (table in [README.md](README.md)).
Limits the same minute (`get-limits?from=XNO&to=USDC-BASE`): min 1.82943 XNO, max 9463.7224 XNO.

## 2. Swap
- Hosted page, no code, no account for the quote: https://nanswap.com/swap/XNO/USDC-BASE (answered HTTP 200).
- By API: `create-order` needs a free Nanswap API key (header `nanswap-api-key`). Getting that key is your operator's step;
  we do not have one and did not create an order, so the order call's exact fields are not reproduced here.
  Read Nanswap's own API documentation for them.

## 3. Verify what you got (read-only)
```
python3 swap_receipt.py --order-id <nanswap order id>
```
Checks both legs on public nodes (the Nano send block and the Base USDC transfer to your address). Exit 0 means both verified.
See [SWAP-RECEIPT.md](SWAP-RECEIPT.md), including its honest limit: the pairing of the two legs is the swap service's record.

## Not measured, so not claimed
How long an XNO-to-USDC order takes end to end, and the fee on a real order beyond the quote: no order was created from
here (spending and keys are the owner's). A single-curl *order* endpoint without an API key was not found.
Where you do not need USDC, [GETTING-ONTO-XNO.md](GETTING-ONTO-XNO.md) shows paying with XNO directly costs no conversion.
