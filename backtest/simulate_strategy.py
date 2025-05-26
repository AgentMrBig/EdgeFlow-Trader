import csv
import datetime
import statistics
import pytz
from collections import defaultdict

DATA_PATH = "usdjpy_m1.csv"
OUTPUT_CSV = "simulated_trades.csv"
CLUSTER_LOG = "trade_clusters.csv"

# Config
SYMBOL = "USDJPY"
TIMEZONE = pytz.timezone("US/Eastern")
MAX_OPEN_TRADES = 4
MA_PERIOD = 10
TRADING_START = datetime.time(7, 30)
TRADING_END = datetime.time(11, 0)
CLUSTER_WINDOW_MINUTES = 5  # if 3+ trades in this window → cluster

class Candle:
    def __init__(self, dt, open_, high, low, close):
        self.dt = dt
        self.open = open_
        self.high = high
        self.low = low
        self.close = close

    def __repr__(self):
        return f"{self.dt} O:{self.open} H:{self.high} L:{self.low} C:{self.close}"

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

# Strategy logic
ma_values = []
entries = []
cluster_counts = defaultdict(int)

for i in range(MA_PERIOD + 2, len(candles)):
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
        entry_time = now.dt
        entry = {
            "timestamp": entry_time.strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": SYMBOL,
            "side": "sell",
            "entry_price": now.close,
            "ma": round(ma, 5)
        }
        entries.append(entry)

        # Cluster detection bucketed by minute
        bucket = entry_time.replace(second=0, microsecond=0)
        cluster_counts[bucket] += 1

# Output trades
with open(OUTPUT_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=entries[0].keys())
    writer.writeheader()
    for row in entries:
        writer.writerow(row)

# Output clusters
with open(CLUSTER_LOG, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Time", "TradeCount"])
    for bucket, count in sorted(cluster_counts.items()):
        if count >= 3:
            writer.writerow([bucket.strftime("%Y-%m-%d %H:%M"), count])

print(f"Simulated {len(entries)} trades. Output saved to {OUTPUT_CSV}")
print(f"Cluster log saved to {CLUSTER_LOG}")
