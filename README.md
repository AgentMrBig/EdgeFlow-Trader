# 🚀 EdgeFlow Trader v0.3

> **A fully-featured trading dashboard + simulation engine for USD/JPY 1-minute scalping with real EdgeFlow logic.**

[![GitHub stars](https://img.shields.io/github/stars/AgentMrBig/EdgeFlow-Trader?style=social)](https://github.com/AgentMrBig/EdgeFlow-Trader/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📑 Table of Contents

- [Overview](#overview)
- [Key Results](#key-results)
- [Screenshot](#screenshot)
- [Features](#features)
- [Quick Start](#quick-start)
- [Dashboard Walkthrough](#dashboard-walkthrough)
- [How It Works](#how-it-works)
- [Current Status](#current-status)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**EdgeFlow Trader** is a complete trading research and simulation platform built around a proven USD/JPY 1-minute scalping strategy. It combines:

- **Powerful backtesting engine** with realistic spreads, margin, cooldown logic, and ATR-based exits
- **Beautiful interactive dashboard** with real-time simulation controls
- **Advanced feature engineering** (HTF bias, MA slope, Stochastic, Bollinger Band width, ATR)
- **Live trading bridge** ready for MT4 integration

---

## Key Results

| Period       | Final Balance     | Net PnL          | Win Rate | Trades |
|--------------|-------------------|------------------|----------|--------|
| **Last 30 Days** | **$5,482,401**    | **+$5,482,301**  | 50.7%    | 3,325  |
| Last 7 Days  | $163,309          | +$163,209        | 49.3%    | 766    |
| Last 3 Days  | $86,762           | +$86,662         | 52.5%    | 322    |
| Last 1 Day   | $90,428           | +$90,328         | 65.2%    | 112    |

> **Starting balance: $100** • Risk: 1.5% per trade • SL: 1.6× ATR • TP: 3.2× ATR

---

## Screenshot

![EdgeFlow Dashboard](https://raw.githubusercontent.com/AgentMrBig/EdgeFlow-Trader/main/screenshots/dashboard-30day.png)

*30-day simulation showing +$5.48 million profit with full control panel and equity curve*

---

## Features

### 🎛️ Simulation Controls
- **Data Range**: Last 1/3/7/30 days or Full backtest
- **Risk per Trade**: 0.5% – 5%
- **Stop Loss / Take Profit**: ATR multipliers (0.5x – 6x)
- **Advanced**: Cooldown after losses, Max hold candles, Session filter (Asia/London/NY/Overlap)

### 📊 Interactive Dashboard
- **Candlestick chart** with 9/20/100/200 SMA + Bollinger Bands
- **Trade markers** (green/red triangles) with hover tooltips
- **Equity curve** with live balance tracking
- **Real-time stats**: Win rate, Net PnL, Max Drawdown, Profit Factor
- **Progress bar + Toast notifications**

### ⚙️ Technical Engine
- Realistic spread (9 points), margin checks, lot sizing
- 15-minute cooldown after 2 consecutive losses
- ATR-based dynamic stop loss & take profit
- Session-aware filtering

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/AgentMrBig/EdgeFlow-Trader.git
cd EdgeFlow-Trader

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the dashboard
cd webapp
python main.py

# 4. Open browser
http://127.0.0.1:8000/dashboard


Dashboard Walkthrough

1. Left Panel — Simulation controls (risk, SL/TP, data range, advanced settings)

2. Center Chart — Candlestick + indicators + trade markers

3. Bottom Chart — Equity curve with running balance

4. Stats Bar — Win rate, PnL, Max Drawdown, Profit Factor (all update live)

How It Works
The system uses the exact same EdgeFlow logic in both backtesting and live mode:

long_signal = (
current['htf_bias'] == 1 and
current['above_ma9'] == 1 and
current['ma9_slope'] > 0 and
current['stoch_k'] < 75 and
current['bb_width'] > rolling_mean
)


All parameters (ATR exits, cooldown, lot sizing, session filters) are identical between simulation and live trading.

Current Status (April 25, 2026)
Component | Status | Notes
--- | --- | ---
Dashboard | ✅ Complete | Full controls + dynamic UI
Simulation Engine | ✅ Complete | Realistic + advanced parameters
Trade Visualization | ✅ Complete | Triangle markers + tooltips
MT4 Bridge | ✅ Ready | File-based communication working
Live Signal Engine | 🚧 In Progress | Logic integration next

Roadmap

* Full live trading integration with MT4 EA
* Real-time signal generation from live ticks
* Genetic optimizer for parameter tuning
* Multi-pair support (XAU/USD as secondary)
* Performance analytics dashboard