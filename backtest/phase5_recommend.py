"""
Phase 5 – Strategy Refinement Suggestions based on trade_analysis.csv
"""

import pandas as pd
from pathlib import Path

# Auto-detect path to trade_analysis.csv
CURRENT_DIR = Path(__file__).parent
TRADE_ANALYSIS_FILE = CURRENT_DIR / "trade_analysis.csv"

# Load enriched trades
df = pd.read_csv(TRADE_ANALYSIS_FILE, parse_dates=["entry_time", "exit_time"])

# Filter trades with valid result
df = df[df["result"].isin(["win", "loss"])]

# Phase 5 Insight Rules
suggestions = []

# 1. Best Time Block to Trade
hourly_winrates = df.groupby("hour")["win"].mean()
best_hour = hourly_winrates.idxmax()
best_winrate = hourly_winrates.max()
suggestions.append(f"✅ Best hour to trade: {best_hour}:00 with win rate {best_winrate:.2%}")

# 2. Avoid Worst Day
day_winrates = df.groupby("day_of_week")["win"].mean()
worst_day = day_winrates.idxmin()
worst_rate = day_winrates.min()
suggestions.append(f"⚠️ Avoid trading on {worst_day} (win rate {worst_rate:.2%})")

# 3. Entry Duration Trim
long_losses = df[(df["result"] == "loss") & (df["duration_min"] > 45)]
if len(long_losses) > 10:
    suggestions.append(f"⏱ Consider closing trades after 45 min to avoid timeouts/losses (found {len(long_losses)} cases)")

# 4. Confirm 8–9am as Optimal Window
if hourly_winrates.get(8, 0) > 0.35 and hourly_winrates.get(9, 0) > 0.3:
    suggestions.append("📈 8–9am ET has >30% win rate. Consider focusing entries during this window.")

# 5. Trade Frequency Guidance
avg_trades_per_hour = df.groupby("hour").size().mean()
suggestions.append(f"📊 Average trades per hour: {avg_trades_per_hour:.2f}")

# Output suggestions
print("\n📋 Strategy Insights – Phase 5 Recommendations:\n")
for s in suggestions:
    print("•", s)
