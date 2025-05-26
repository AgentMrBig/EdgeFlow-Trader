import csv
import datetime
import statistics
import pytz
import matplotlib.pyplot as plt
from collections import defaultdict

DATA_PATH = "usdjpy_m1.csv"
OUTPUT_CSV = "simulated_trades.csv"
PERFORMANCE_LOG = "timeblock_profit.csv"
EQUITY_CURVE_PNG = "equity_curve.png"

# Config
SYMBOL = "USDJPY"
TIMEZONE = pytz.timezone("US/Eastern")
MA_PERIOD = 10
TRADING_START = datetime.time(7, 30)
TRADING_END = datetime.time(11, 0)
TP_PIPS = 15
SL_PIPS = 10
PIP_SCALE = 0.01
LOT_SIZE = 0.25
PIP_VALUE_PER_LOT = 10  # approx $10 per pip for 1.0 lot on USDJPY

class Candle:
    def __init__(self, dt, open_, high, low, close):
        self.dt = dt
        self.open = open_
        self.high = high
        self.low = low
        self.close = close

# Load candles
candles = []
with open(DATA_PATH) as f:
    reader = csv.reader(f)
    next(reader)  # skip header
    for row in reader:
        if len(row) != 7: continue
        date_str, time_str = row[0], row[1]
        dt = datetime.datetime.strptime(date_str + time_str, "%Y%m%d%H:%M:%S")
        dt = pytz.utc.localize(dt).astimezone(TIMEZONE)
        o, h, l, c = map(float, row[2:6])
        candles.append(Candle(dt, o, h, l, c))

entries = []
profit_by_time = defaultdict(lambda: {"trades": 0, "wins": 0, "losses": 0})

cumulative_profit = 0.0
balance_history = []

for i in range(MA_PERIOD + 2, len(candles) - 60):
    now = candles[i]
    if not (TRADING_START <= now.dt.time() <= TRADING_END):
        continue

    closes = [c.close for c in candles[i-MA_PERIOD:i]]
    ma = statistics.mean(closes)

    prev = candles[i-1]
    prev2 = candles[i-2]

    broke_below_ma = prev2.close > ma and prev.close < ma
    retest_ma = prev.high >= ma
    broke_low = now.low < min(prev.low, prev2.low)

    if broke_below_ma and retest_ma and broke_low:
        entry_price = now.close
        tp = entry_price - TP_PIPS * PIP_SCALE
        sl = entry_price + SL_PIPS * PIP_SCALE
        result = "timeout"
        exit_price = entry_price
        pnl = 0.0

        for j in range(i+1, i+60):
            future = candles[j]
            if future.low <= tp:
                result = "win"
                exit_price = tp
                pnl = TP_PIPS * LOT_SIZE * PIP_VALUE_PER_LOT
                break
            elif future.high >= sl:
                result = "loss"
                exit_price = sl
                pnl = -SL_PIPS * LOT_SIZE * PIP_VALUE_PER_LOT
                break

        hour_block = now.dt.strftime("%H:%M")
        profit_by_time[hour_block]["trades"] += 1
        if result == "win":
            profit_by_time[hour_block]["wins"] += 1
        elif result == "loss":
            profit_by_time[hour_block]["losses"] += 1

        cumulative_profit += pnl
        balance_history.append((now.dt, cumulative_profit))

        entries.append({
            "timestamp": now.dt.strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": SYMBOL,
            "side": "sell",
            "entry_price": round(entry_price, 5),
            "exit_price": round(exit_price, 5),
            "result": result,
            "pnl": pnl
        })

with open(OUTPUT_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=entries[0].keys())
    writer.writeheader()
    writer.writerows(entries)

with open(PERFORMANCE_LOG, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["HourBlock", "Trades", "Wins", "Losses", "WinRate(%)"])
    for hour in sorted(profit_by_time):
        stats = profit_by_time[hour]
        trades = stats["trades"]
        wins = stats["wins"]
        losses = stats["losses"]
        win_rate = (wins / trades * 100) if trades else 0
        writer.writerow([hour, trades, wins, losses, f"{win_rate:.2f}"])

# Plot equity curve
if balance_history:
    x_vals = [t[0] for t in balance_history]
    y_vals = [t[1] for t in balance_history]

    plt.figure(figsize=(10, 5))
    plt.plot(x_vals, y_vals, label="Equity Curve", color="blue")
    plt.xlabel("Time")
    plt.ylabel("Cumulative P&L ($)")
    plt.title("Equity Curve – EdgeFlow Strategy")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(EQUITY_CURVE_PNG)
    print(f"Equity curve saved to {EQUITY_CURVE_PNG}")

print(f"Simulated {len(entries)} trades with TP/SL. Saved to {OUTPUT_CSV}")
print(f"Hourly profit breakdown saved to {PERFORMANCE_LOG}")
