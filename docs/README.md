# EdgeFlow Trader

> **Mission:** Transform a discretionary USDJPY scalping edge into a fully-automated, AI-enhanced trading machine that runs 24/5 on MT4.

---

## 1 Project Snapshot

| Piece                                 | Status       | Notes |
|--------------------------------------|--------------|-------|
| **MT4 EA** – tick logger & listener  | ✅ v0.2       | Logs ticks, executes orders from JSON bridge |
| **Python Bridge** – CSV ↔ DB ↔ REST  | ✅ v0.1d      | FastAPI app receives/post orders, routes to EA |
| **TimescaleDB**                      | ✅            | Docker container `edgeflow-timescaledb` |
| **Backtester / Strategy Sim**        | ✅            | Pattern-based rule engine with SR awareness |
| **Trade Enrichment & Summary**       | ✅            | Hour/day insights, SR proximity, duration |
| **Genetic Optimizer**                | ✅ Sprint-3   | Evolves MA/TP/SL/tolerance via simulate_pnl |
| **Web Dashboard**                    | ✅            | Visual P&L, win rate, trade summaries |
| **Order execution logic**            | ✅ Sprint-1   | MQL4 EA parses and executes JSON |
| **Risk engine / sizing rules**       | ✅ Sprint-1   | Starts 0.25 lots, +0.25 per $200 balance |

---

## 2 Quick Start (Local Dev)

```bash
git clone https://github.com/AgentMrBig/EdgeFlow-Trader.git
cd EdgeFlow-Trader

# Start DB
docker compose -f docker/timescaledb-compose.yml up -d

# Attach EA
# MetaEditor → open ea/EdgeFlowTrader.mq4 → Compile
# Attach to USDJPY M1 chart, enable Auto-Trading

# Start bridge
cd bridge
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt
python main.py
```

### Smoke Test

```bash
curl -X POST http://localhost:8000/order      -H "Content-Type: application/json"      -d '{"symbol":"USDJPY","side":"buy","lot":0.01}'
```

Check MT4 *Experts* tab for confirmation.

---

## 3 Backtest & Strategy Optimizer

### Run Backtest
```bash
cd backtest
python simulate_pnl.py
```

Generates:
- `simulated_trades.csv`
- `timeblock_profit.csv`
- `equity_curve.png`

### Run Optimizer (Genetic Algorithm)
```bash
python strategy_optimizer.py
```

Tracks top-performing MA/TP/SL configurations over generations using total PnL. Avoids timeout clutter and supports SR-based entry filtering.

---

## 4 Web Dashboard

```bash
cd webapp
uvicorn main:app --reload
```

Navigate to `http://127.0.0.1:8000`:

- View total trades, win rate, cumulative P&L
- Chart-based equity curve (Chart.js)
- Interactive stats by time and day

---

## 5 Repo Structure

```text
EdgeFlow-Trader/
├─ ea/                         – MQL4 Expert Advisor source
├─ bridge/                     – FastAPI MT4 bridge
├─ backtest/                   – strategy engine, analyzer, optimizer
│   ├─ simulate_pnl.py         – Simulates trades, supports rules + SR logic
│   ├─ trade_analyzer.py       – Adds time/day/win-rate insight
│   ├─ trade_summary.py        – Prints key stats (avg win/loss, durations, freq)
│   ├─ trade_enhancer.py       – SR scoring, trend labels, enriched trade data
│   ├─ strategy_optimizer.py   – Genetic optimizer using simulate_pnl
│   └─ support_resistance_detector.py – Multi-TF S/R zone detection
├─ webapp/                     – FastAPI + Jinja2 + Chart.js UI
├─ docker/
│   └─ timescaledb-compose.yml
├─ docs/
│   ├─ techdoc.md              – design + dev notes
│   ├─ protocol.md             – tick / order schema
│   └─ risk-config.yaml        – lot sizing & scaling
└─ README.md
```

---

## 6 Recent Results (Sample)

```
✔️ Best PnL from optimizer: $15,187.50
✔️ Ideal settings found: MA=8, TP=29, SL=36
✔️ High trade cluster: 8–9am ET, SR confirmed
✔️ Timeout reduction via equity target-based exits
```

---

## 7 Commit Strategy

* **`main`** = stable release after full sprint.
* Feature → `dev` → squash-merge into `main` when stable.
* Use tags like `feat:`, `fix:`, `doc:`, `refactor:` in commit messages.

---

## 8 Strategy Improvement Log: Smart Exits & Margin Reality

The most recent simulation improvements were implemented to address several critical issues observed in earlier versions of the strategy engine.

### 🔧 Key Enhancements

- **Margin Stop-Out Simulation**:  
  The strategy now halts immediately if the margin level drops below 25%, mimicking a real broker margin call.
  - Prevents unrealistic "survival" of blown accounts
  - Outputs final equity and halts the simulation

- **Trailing Stop Only After Breakeven**:  
  Trailing stops are now only activated after a trade is in at least +5 pips of profit.

- **Smart Exit After Decay**:  
  Trades still in loss after 15 candles are evaluated against support/resistance zones from derived 5-minute data.  
  - If no S/R is nearby to justify staying in the trade, the position is closed to prevent deepening losses.

### 🧪 Example Run Result

```
💥 Margin call triggered at 2023-09-27 14:51:00. Account busted. Final equity: $0.45
Simulation complete. Trades executed: 54
```

Although not yet profitable, this setup now:
- Reflects true trade risk and leverage exposure
- Is better suited for genetic optimization
- Rejects trades that deteriorate beyond their window of opportunity
