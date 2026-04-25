# EdgeFlow Trader

> **Mission**: Transform a discretionary USD/JPY 1m scalping edge into a fully-automated, robust, and profitable trading system that runs 24/5 on MT4, with XAU/USD as a high-spread support pair.

**Current Status (April 22, 2026)**:  
We have successfully merged the best parts of EdgeFlow-Trader infrastructure with AlphaScan feature engineering. The system is now generating **strong backtest results** (+$140k from $10k and +$80k from $100 starting balance) using "All sessions".

---

## 1. Project Snapshot

| Piece                                 | Status       | Notes |
|--------------------------------------|--------------|-------|
| **MT4 EA + Bridge**                  | ✅           | JSON-based order execution ready |
| **Feature Engineering**              | ✅           | `feature_engineer.py` — CORE MT4 indicators + AlphaScan enhancements on 60-candle window |
| **Backtester**                       | ✅ Improved  | `simulate_edgeflow.py` — dynamic ATR sizing, session control, realistic $100 start |
| **Risk Engine**                      | ✅           | 1% risk per trade, dynamic lot sizing |
| **Genetic Optimizer**                | ✅           | Ready for tuning |
| **Web Dashboard**                    | ✅           | Available |
| **Visual Chart Renderer**            | In Progress  | Planned next |
| **Live Execution**                   | In Progress  | Bridge + EA ready, logic integration next |

**Best Result So Far**:
- Starting Balance: $100
- Sessions: All
- Net PnL: **+$80,872**
- Win Rate: ~33.6%

---

## 2. Core Technical Foundation

- **Timeframe**: 1-minute (M1)
- **Decision Window**: Exactly 60 completed candles (last full hour)
- **Indicators**: Bollinger Bands (20,2), 9/20/100/200 SMA, Stochastic (5,3,3), ATR(14)
- **Key Filters**: Higher-TF bias, session filtering, BB expansion
- **Risk**: 1% per trade with dynamic ATR-based lot sizing

---

## 3. Current Architecture

```mermaid
flowchart TD
    A[Raw 1m Candles<br>MT4 EA Bridge] --> B[TimescaleDB + Rolling DataFrame]
    B --> C[feature_engineer.py<br>CORE + AlphaScan features]
    C --> D[Session Filter + Higher-TF Bias]
    D --> E[Decision Engine<br>simulate_edgeflow.py]
    E --> F[Risk Management + Execution]
    F --> G[MT4 EA via JSON]
    G --> H[Results + Equity Curve + Dashboard]

## 4. High-Level Architecture (Final Target)

```mermaid
flowchart TD
    A[Raw 1m Candles<br>MT4 EA Bridge] --> B[TimescaleDB + Rolling In-Memory DataFrame]
    B --> C[Feature Engineering<br>CORE indicators + AlphaScan enhancements]
    C --> D[Higher-TF Bias + Session Filter + Regime Detection (optional)]
    D --> E[Decision Engine<br>Rule-based + future ML scoring]
    E --> F[Risk & Order Management<br>dynamic lots, SL/TP, max trades/hour]
    F --> G[MT4 EA Execution<br>via JSON Bridge]
    G --> H[Enrichment + Dashboard + Visual Chart Renderer<br>annotated MT4-style charts]


## 5. Development Priorities (Current Sprint)

1. **Bridge Enhancement** – Ensure reliable 1m candle broadcast + order execution  
2. **Indicator Engine** – Exact pandas implementation of CORE_CHART_SETUP + AlphaScan features on 60-candle window  
3. **Visual Debugger** – Render candlestick charts with all indicators + bot signals overlaid  
4. **Backtest Integration** – Merge AlphaScan features into `simulate_pnl.py` and `simulate_edgeflow.py`  
5. **Dynamic Risk Sizing** – ATR-based, pair-specific for USD/JPY and XAU/USD (already implemented in simulate_edgeflow.py)  
6. **Session Analysis & Optimization** – Run controlled tests across All / Asia / London+NY+Overlap to understand contribution  
7. **Drawdown Reduction & Entry Refinement** – Improve equity curve smoothness and win rate while maintaining profitability  
8. **Visual Chart Renderer** – Create annotated MT4-style charts with bot signals for debugging  

---

**Version**: 1.1 – Profit-Focused Integration  
**Date**: April 22, 2026  
**Focus Pair**: USD/JPY (primary) | XAU/USD (support)  
**Current Best Result**: +$140,303 Net PnL (All sessions) from $10k start | +$80,872 from $100 start