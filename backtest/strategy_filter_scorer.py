# strategy_filter_scorer.py
import pandas as pd

# Load enriched trade data
INPUT_CSV = "ttp_ptr_enriched_trades.csv"
df = pd.read_csv(INPUT_CSV, parse_dates=["entry_time", "exit_time"])

# === Filter Settings ===
MIN_TTP = 0          # in minutes
MAX_TTP = 5          # None = no upper limit
REQUIRE_PTR = False  # Only include losses that were in profit
HOURS = [8, 9]       # Only trades from 8am to 9:59am
DAYS = ["Tuesday", "Wednesday", "Thursday", "Friday"]

# === Apply Filters ===

# Filter by hour
df["hour"] = df["entry_time"].dt.hour
df = df[df["hour"].isin(HOURS)]

# Filter by day of week
df["day"] = df["entry_time"].dt.day_name()
df = df[df["day"].isin(DAYS)]

# Filter by TTP (wins only)
def ttp_filter(row):
    if row["result"] == "win":
        if pd.isna(row["time_to_profit_min"]):
            return False
        if row["time_to_profit_min"] < MIN_TTP:
            return False
        if MAX_TTP is not None and row["time_to_profit_min"] > MAX_TTP:
            return False
    return True

df = df[df.apply(ttp_filter, axis=1)]

# Filter by PTR (losses only)
if REQUIRE_PTR:
    df = df[(df["result"] != "loss") | (df["profit_then_reverse"] == True)]

# === Score the filtered results ===
total = len(df)
wins = len(df[df["result"] == "win"])
losses = len(df[df["result"] == "loss"])
timeouts = len(df[df["result"] == "timeout"])
win_rate = (wins / total * 100) if total > 0 else 0
avg_pnl = df["pnl"].mean() if total > 0 else 0

# === Report ===
print("🎯 Filtered Strategy Results")
print(f"• Trades analyzed: {total}")
print(f"• Wins: {wins} | Losses: {losses} | Timeouts: {timeouts}")
print(f"• Win Rate: {win_rate:.2f}%")
print(f"• Average PnL: ${avg_pnl:.2f}")
