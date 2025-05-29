# profit_onset_analyzer.py
# Phase 1: TTP (Time-To-Profit) Analyzer

import pandas as pd
from datetime import datetime, timedelta
import csv

# Load trades
TRADES_CSV = "simulated_trades.csv"
CANDLES_CSV = "usdjpy_m1.csv"
OUTPUT_CSV = "ttp_ptr_enriched_trades.csv"

# PIP scale (0.01 for USDJPY)
PIP_SCALE = 0.01

# Load candle data
candles = []
with open(CANDLES_CSV, newline='') as f:
    reader = csv.reader(f)
    next(reader)  # skip header
    for row in reader:
        if len(row) < 6:
            continue
        date_str, time_str = row[0], row[1]
        dt = datetime.strptime(date_str + time_str, "%Y%m%d%H:%M:%S")
        o, h, l, c = map(float, row[2:6])
        candles.append({"dt": dt, "open": o, "high": h, "low": l, "close": c})

# Convert to DataFrame for quick lookup
df_candles = pd.DataFrame(candles).set_index("dt")

# Load simulated trades
df_trades = pd.read_csv(TRADES_CSV, parse_dates=["entry_time", "exit_time"])

# Helper to get first candle where TP would have been hit
def get_time_to_tp(entry_time, side, tp_price):
    subset = df_candles.loc[entry_time: entry_time + timedelta(hours=1)]
    for i, row in subset.iterrows():
        if side == "buy" and row["high"] >= tp_price:
            return (i - entry_time).total_seconds() / 60
        elif side == "sell" and row["low"] <= tp_price:
            return (i - entry_time).total_seconds() / 60
    return None  # never hit TP

# Helper to check if loss trade was ever in profit (PTR)
def check_profit_then_reverse(entry_time, side, entry_price, tp):
    subset = df_candles.loc[entry_time: entry_time + timedelta(hours=1)]
    for _, row in subset.iterrows():
        if side == "buy" and row["high"] >= tp:
            return True
        elif side == "sell" and row["low"] <= tp:
            return True
    return False

# Enrich trades with TTP and PTR
ttp_results = []
ptr_results = []

for _, trade in df_trades.iterrows():
    if trade["result"] == "win":
        ttp = get_time_to_tp(trade["entry_time"], trade["side"], trade["tp"])
        ttp_results.append(ttp)
        ptr_results.append(None)
    elif trade["result"] == "loss":
        ptr = check_profit_then_reverse(trade["entry_time"], trade["side"], trade["entry_price"], trade["tp"])
        ptr_results.append(ptr)
        ttp_results.append(None)
    else:
        ttp_results.append(None)
        ptr_results.append(None)

df_trades["time_to_profit_min"] = ttp_results
df_trades["profit_then_reverse"] = ptr_results

# Save enriched trades
df_trades.to_csv(OUTPUT_CSV, index=False)
print(f"✅ TTP/PTR enriched trades saved to {OUTPUT_CSV}")

# Optional summary
valid_ttps = df_trades["time_to_profit_min"].dropna()
ptr_losses = df_trades[df_trades["profit_then_reverse"] == True]

if not valid_ttps.empty:
    print("\n📈 TTP Summary:")
    print(f"• Average TTP: {valid_ttps.mean():.2f} min")
    print(f"• Median TTP: {valid_ttps.median():.2f} min")
    print(f"• Fastest win: {valid_ttps.min():.1f} min")
    print(f"• Slowest win: {valid_ttps.max():.1f} min")

if not ptr_losses.empty:
    print("\n📉 PTR Summary:")
    print(f"• Total losses that were in profit first: {len(ptr_losses)}")
    print(f"• Percent of losses with PTR: {100 * len(ptr_losses) / len(df_trades[df_trades['result'] == 'loss']):.2f}%")
