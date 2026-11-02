// The page's arithmetic must equal the Python tool's on a grid (the page cannot drift from the tested code).
const assert = require("assert"), { execFileSync } = require("child_process"), core = require("./breakeven-core.js");
for (const [p, n, g] of [[0.01, 5000, 0.002], [0.03, 1000, 0.0005], [10, 100, 0.002], [0.5, 50, 0.01]]) {
  const py = JSON.parse(execFileSync("python3", ["breakeven.py", "--price-usd", String(p), "--calls", String(n), "--gas-usd", String(g), "--json"]));
  const js = core.perCall(p, n, g);
  assert(Math.abs(py.xno_usd_per_call - js.xno_usd_per_call) < 1e-12, "xno " + p);
  assert.strictEqual(py.cheaper, js.cheaper);
  const be = core.breakEvenPrice(n, g);
  assert(Math.abs(py.break_even_price_usd - be) / be < 1e-9, "be " + p);
}
console.log("ok page == tool on 4 cases");
