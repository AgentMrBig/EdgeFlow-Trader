# EdgeFlow Trader

> **Mission**: Transform a discretionary USD/JPY 1m scalping edge into a fully-automated, robust, and profitable trading system that runs 24/5 on MT4, with XAU/USD as a high-spread support pair.

**Current Status (April 22, 2026)**:  
We have successfully integrated rich feature engineering from AlphaScan with EdgeFlow-Trader’s infrastructure. The system is now producing strong backtest results using a 60-candle decision window and dynamic risk sizing.

**Best Results So Far**:  
- Starting Balance $10,000 → +$140,303 Net PnL (All sessions)  
- Starting Balance $100 → +$80,872 Net PnL (All sessions)

---

## 1. Project Snapshot

| Piece                                 | Status              | Notes |
|--------------------------------------|---------------------|-------|
| **MT4 EA + Bridge**                  | ✅                  | JSON-based execution |
| **Feature Engineering**              | ✅                  | feature_engineer.py — CORE MT4 indicators + AlphaScan enhancements |
| **Backtester**                       | ✅ Improved         | simulate_edgeflow.py — realistic $100 start, session control |
| **Risk Engine**                      | ✅                  | 1% risk per trade, ATR-based dynamic lots |
| **Genetic Optimizer**                | ✅                  | Ready for tuning |
| **Web Dashboard**                    | ✅                  | Available |
| **Visual Chart Renderer**            | In Progress         | High priority next |
| **Live Execution**                   | In Progress         | Bridge ready, logic integration next |

---

## 2. Core Technical Foundation

- Timeframe: 1-minute (M1)  
- Decision Window: Exactly 60 completed candles (last full hour)  
- Indicators: Bollinger Bands (20,2), 9/20/100/200 SMA, Stochastic (5,3,3), ATR(14)  
- Key Filters: Higher-TF bias, BB expansion, session filtering  
- Risk: 1% per trade with dynamic ATR-based lot sizing

---

## 3. Quick Start (Backtesting)

cd backtest
python simulate_edgeflow.py

To change session mode, edit this line in simulate_edgeflow.py:
TRADE_SESSIONS = "All"        # Options: "All", "Asia", "London", "New York", "Overlap", or list like ["London", "New York", "Overlap"]

---

## 4. Development Priorities (Current Sprint)

1. Session Analysis — Run controlled tests (All vs Asia vs London+NY+Overlap) to understand contribution of each session  
2. Drawdown Reduction — Improve equity curve smoothness while maintaining high profitability  
3. Entry Logic Refinement — Add ma9_hold_duration, engulfing, and stronger MA alignment  
4. Visual Debugger — Create annotated MT4-style charts with bot signals for debugging  
5. Live Bridge Integration — Connect the decision logic to the MT4 EA for paper/live trading  
6. Genetic Optimizer Tuning — Optimize key parameters on the new feature set  

---

## 5. Backup & Restore

We have a backup system in place:

# Create a timestamped backup of current simulate_edgeflow.py
python backup_simulate.py

# Restore the latest backup
python backup_simulate.py restore

Current Last Known Good version (All sessions, +$140k from $10k / +$80k from $100) is backed up as of April 22, 2026.

---

**Focus Pair**: USD/JPY (primary) | XAU/USD (support)  
**Version**: 1.2 – Profit-Focused Integration  
**Date**: April 22, 2026