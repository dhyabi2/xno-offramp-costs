// Same arithmetic as breakeven.py (tested against it by test_breakeven.js). No network.
const CURVE = [[1, 7.52], [10, 1.78], [100, 1.02], [1000, 0.96]]; // [usd_in, spread % vs CoinGecko], Nanswap USDC-BASE -> XNO, measured 2026-11-02T09:10Z
function spreadPct(F){ if(F<=CURVE[0][0])return CURVE[0][1]; const L=CURVE[CURVE.length-1]; if(F>=L[0])return L[1];
  for(let i=0;i<CURVE.length-1;i++){const [a,ca]=CURVE[i],[b,cb]=CURVE[i+1]; if(a<=F&&F<=b){const t=(Math.log(F)-Math.log(a))/(Math.log(b)-Math.log(a));return ca+t*(cb-ca);}} }
function perCall(price,calls,gas,cashOutPct=0){ const F=price*calls,s=spreadPct(F),xno=price*(s+cashOutPct)/100+gas/calls;
  return {float_usd:F,spread_pct:s,base_usd_per_call:gas,xno_usd_per_call:xno,cheaper:xno<gas?"xno":"base"}; }
function breakEvenPrice(calls,gas,cashOutPct=0){ let lo=1e-6,hi=1e5; const f=p=>perCall(p,calls,gas,cashOutPct).xno_usd_per_call-gas;
  if(f(lo)>=0)return null; if(f(hi)<0)return hi; for(let i=0;i<200;i++){const m=Math.sqrt(lo*hi); if(f(m)<0)lo=m; else hi=m;} return lo; }
if(typeof module!=="undefined")module.exports={perCall,breakEvenPrice,spreadPct};
