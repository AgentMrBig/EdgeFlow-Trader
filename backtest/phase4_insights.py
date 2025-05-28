from pathlib import Path
import pandas as pd

# Automatically detect correct path
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
TRADE_ANALYSIS_FILE = (ROOT_DIR / "backtest" / "trade_analysis.csv").resolve()

# Load and display top insights
df = pd.read_csv(TRADE_ANALYSIS_FILE)

# Top 5 highest PnL trades
top_winners = df.sort_values(by="pnl", ascending=False).head(5)

# Longest duration losses
long_losses = df[df["win"] == False].sort_values(by="duration_min", ascending=False).head(5)

# Entry hours with win rate over 50%
high_win_hours = df.groupby("hour")["win"].mean().reset_index()
high_win_hours = high_win_hours[high_win_hours["win"] > 0.5]

print("\n🔥 Top 5 Winning Trades:")
print(top_winners[["entry_time", "symbol", "pnl", "duration_min", "result"]])

print("\n💀 Longest Duration Losses:")
print(long_losses[["entry_time", "symbol", "pnl", "duration_min", "result"]])

print("\n🕐 Hours With Win Rate > 50%:")
print(high_win_hours.rename(columns={"win": "win_rate"}))
