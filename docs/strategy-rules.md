# strategy-rules.md  
*EdgeFlow Trader – Rule-Based Strategy v0.1*  
**Version:** 0.1  
**Status:** Active  
**Target Market:** USDJPY  
**Timeframe:** M1  
**Execution Mode:** Live & Backtest Ready

---

## 🎯 Strategy Overview

This strategy is based on **aggressive scalping** using price action, the **10-period moving average**, and key **support/resistance levels**.

It aims to enter short trades during micro-trend breakdowns, especially when price uses the 10MA as dynamic resistance before breaking a previous swing low.

---

## 📈 Entry Criteria (Sell Setup)

| Condition | Description |
|----------|-------------|
| **1. MA Break** | Price **closes below** the 10-period moving average (red line). |
| **2. Retest** | Price **retraces back to the 10MA**, slightly touches or pierces it. |
| **3. Break of Low** | Price then **moves down and breaks a previous swing low**. |
| **4. Confirmation Window** | Time must be between **7:30 AM – 11:00 AM EST**. |
| **5. No Overlap** | Max 4 trades open — no entry if already at limit. |

---

## 🛠 Technical Details

| Element | Value / Rule |
|--------|---------------|
| **Symbol** | `USDJPY` |
| **Timeframe** | `M1` |
| **Moving Average** | Simple 10-period (based on close) |
| **Max Open Trades** | 4 (controlled by bridge logic) |
| **Lot Size** | Dynamic, based on `risk-config.yaml`:<br>Start = 0.25 lots<br>+0.25 lots per $200 balance increase |
| **Slippage** | From config (`slippagePoints`), default = 3 |
| **Stop Loss** | Not fixed — determined by S/R (future upgrade) |
| **Take Profit** | None — exit manually or by logic (future upgrade) |
| **Magic Number** | 12345 (static, for tracking) |

---

## 💡 Strategic Notes

- No trades are taken if all entry criteria aren’t met.
- Time filter helps avoid false breakouts in low-volume periods.
- Future versions may include:
  - Volatility filters (e.g., ATR threshold)
  - Stochastic or volume overlays
  - Exit triggers based on 10MA crossback or RR target

---

## 🧪 Backtest Requirements

To test this strategy offline:

- Must have `ticks.csv` with at least **1 week of M1 data**
- Use simulation script to:
  - Scan for entry triggers
  - Log "would-be" orders to file
  - Compare performance against real trades (if available)

---

## 📦 Version History

| Version | Notes |
|---------|-------|
| **0.1** | Initial live-capable version with MA + breakout logic |
| *(next)* | Add SL/TP logic, trailing, multi-timeframe filters |

---

*© 2025 EdgeFlow Trader — Strategy Core*
