# Yuvi-N-Short/Long (MasterV6) - Pine Script Reference

> **This file is the SINGLE SOURCE OF TRUTH for all strategy logic.**
> Any Python implementation MUST match this exactly.

## Quick Reference

| Section | Pine Lines | Key Functions |
|---------|-----------|---------------|
| 1. Setup | 1-15 | Index selection, expiry, date range |
| 2. Strikes | 16-25 | 5 strike slots (ITM2→OTM2) |
| 3. Logic | 26-40 | calcMode, chop filter, momentum/trend toggles |
| 4. Short Strategy | 41-55 | SL/TSL/Smart SL/Time Exit |
| 5. Long Strategy | 56-75 | Strict entry, scope restrict |
| 6. Visuals | 76-95 | Table positions, overlays |
| 7. Account | 96-98 | Capital, lot size |
| 8. Alerts | 99-110 | Stoxxo format |
| Data Processing | 111-180 | getOC, buildSym, day open tracking |
| Indicators | 181-230 | RSI, ROC, DMI/ADX, Chop, SuperTrend, EMA, VWAP, VWMA |
| Regime Engine | 231-260 | calcRegime, calcTType, getMode, getIndReg |
| Directional State | 261-280 | bull/bear building/active |
| Signal Engine | 281-350 | procSignal - buy/sell conditions |
| Trade State Machine | 351-700 | Per-strike short/long entry/exit logic |
| P&L Table | 701-end | Account summary, floating P&L, history |

## Key Logic Details

### Per-Strike State Variables (×5 strikes)
- `lSig` (0=flat, -1=short active)
- `lSigLong` (0=flat, 2=long active)
- `ep` / `epLong` (entry prices)
- `et` / `xt` (entry/exit times)
- `banked` (realized P&L points)
- `ll` / `hh` (lowest low / highest high for TSL)
- `slSafe` (smart SL disable flag)
- `isLong` (direction flag)
- `cntShort` / `cntLong` (trade counters)

### Short Exit Priority Order
1. Time Exit (hard exit)
2. Target Hit
3. Smart Guard Exit (TSL active + close > EMA & VWMA)
4. TSL Hit
5. Smart SL Disable (sets slSafe flag)
6. Fixed SL Hit (only if !slSafe)
7. Buy signal reversal exit

### Long Exit Priority Order
1. Time Exit
2. Target Hit
3. Fixed SL Hit
4. TSL Hit
5. Structure Break (close < EMA & VWMA & VWAP)
6. Panic Exit (close < VWAP < VWMA)

### procSignal() Logic
- **Buy**: (strict: close>EMA AND (close>VWAP OR close>VWMA)) + RSI>40 + DI+>DI- + ROC>0, OR (close>VWAP AND VWAP>VWMA)
- **Sell**: Old logic (momentum) AND/OR New logic (trend crossover) AND/OR VWAP reversal
- **Chop filter**: blocks signals when chop > chopLimit (e.g. 61.8)
- **Crossover Window**: New logic requires a crossover within `crossoverWindow` bars.

### Signal Execution Guarantees (barstate.isconfirmed)
- Pine Script exclusively processes signal evaluations and trade state transitions on **candle close** using `if barstate.isconfirmed`.
- No signals are generated intra-bar (during an open, ticking candle). 
- Python polling mimics this by sampling only after the minute boundary.

### Backtest / Replay Bounding
- Pine Script filters out all signals outside the user's defined date range using `inBacktestRange`.
- The frontend P&L table filters out backfill trades and shows strictly the current day's trades to match Pine's behavior.

### Daily Reset
- **All** state variables reset on `ta.change(time("D"))!=0` (start of the trading session).
- This resets trade counters (`cntShort`, `cntLong`), the floating `banked` P&L for the day, and any active `lSig` state flags, ensuring each day starts with a blank slate.
