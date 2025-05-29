# File: simulate_pnl.py
# ✅ This version includes 'silent' parameter and properly places the return block inside the function.

import csv
import datetime
import statistics
import pytz
import matplotlib.pyplot as plt
import pandas as pd
from support_resistance_detector import get_support_resistance_zones
from collections import defaultdict

TIMEZONE = pytz.timezone("US/Eastern")
SYMBOL = "USDJPY"
DATA_PATH = "usdjpy_m1.csv"
PIP_SCALE = 0.01
PIP_VALUE_PER_LOT = 10
LOT_SIZE = 0.25

class Candle:
    def __init__(self, dt, open_, high, low, close):
        self.dt = dt
        self.open = open_
        self.high = high
        self.low = low
        self.close = close

def load_candles():
    candles = []
    with open(DATA_PATH) as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) != 7: continue
            date_str, time_str = row[0], row[1]
            dt = datetime.datetime.strptime(date_str + time_str, "%Y%m%d%H:%M:%S")
            dt = pytz.utc.localize(dt).astimezone(TIMEZONE)
            o, h, l, c = map(float, row[2:6])
            candles.append(Candle(dt, o, h, l, c))
    return candles

def is_near_sr(price, zones, tolerance=0.002):
    nearby = [level for level in zones['support'] + zones['resistance'] if abs(price - level) < price * tolerance]
    return len(nearby) > 0

def simulate_strategy(ma_period=10, tp_pips=15, sl_pips=10,
                      trading_start=datetime.time(7, 30),
                      trading_end=datetime.time(11, 0),
                      output_csv="simulated_trades.csv",
                      performance_log="timeblock_profit.csv",
                      equity_curve_png="equity_curve.png",
                      proximity_tolerance=0.002,
                      silent=False):

    candles = load_candles()
    df = pd.DataFrame([{
        'datetime': c.dt,
        'open': c.open,
        'high': c.high,
        'low': c.low,
        'close': c.close,
        'volume': 0
    } for c in candles])

    zones = get_support_resistance_zones(df, timeframes=['1h', '4h', '1d'])

    entries = []
    profit_by_time = defaultdict(lambda: {"trades": 0, "wins": 0, "losses": 0})
    cumulative_profit = 0.0
    balance_history = []

    for i in range(ma_period + 2, len(candles) - 60):
        now = candles[i]
        if not (trading_start <= now.dt.time() <= trading_end):
            continue

        closes = [c.close for c in candles[i - ma_period:i]]
        ma = statistics.mean(closes)
        prev = candles[i - 1]
        prev2 = candles[i - 2]

        trade_type = None
        reasons = []

        if prev2.close > ma and prev.close < ma:
            if prev.high >= ma:
                if now.low < min(prev.low, prev2.low):
                    if is_near_sr(now.close, zones, tolerance=proximity_tolerance):
                        trade_type = "sell"
                    else: reasons.append("near_sr")
                else: reasons.append("broke_low")
            else: reasons.append("retest_ma")
        else: reasons.append("broke_below_ma")

        if not trade_type:
            reasons = []
            if prev2.close < ma and prev.close > ma:
                if prev.low <= ma:
                    if now.high > max(prev.high, prev2.high):
                        if is_near_sr(now.close, zones, tolerance=proximity_tolerance):
                            trade_type = "buy"
                        else: reasons.append("near_sr")
                    else: reasons.append("broke_high")
                else: reasons.append("retest_ma")
            else: reasons.append("broke_above_ma")

        if not trade_type:
            if not silent:
                print(f"[Skip] {now.dt.strftime('%Y-%m-%d %H:%M:%S')} - Failed: {', '.join(reasons)}")
            continue

        entry_price = now.close
        tp = entry_price + tp_pips * PIP_SCALE if trade_type == "buy" else entry_price - tp_pips * PIP_SCALE
        sl = entry_price - sl_pips * PIP_SCALE if trade_type == "buy" else entry_price + sl_pips * PIP_SCALE

        result = "timeout"
        exit_price = entry_price
        pnl = 0.0
        exit_time = now.dt

        for j in range(i + 1, i + 60):
            future = candles[j]
            if trade_type == "sell" and future.low <= tp:
                result = "win"; exit_price = tp; pnl = tp_pips * LOT_SIZE * PIP_VALUE_PER_LOT; exit_time = future.dt; break
            elif trade_type == "sell" and future.high >= sl:
                result = "loss"; exit_price = sl; pnl = -sl_pips * LOT_SIZE * PIP_VALUE_PER_LOT; exit_time = future.dt; break
            elif trade_type == "buy" and future.high >= tp:
                result = "win"; exit_price = tp; pnl = tp_pips * LOT_SIZE * PIP_VALUE_PER_LOT; exit_time = future.dt; break
            elif trade_type == "buy" and future.low <= sl:
                result = "loss"; exit_price = sl; pnl = -sl_pips * LOT_SIZE * PIP_VALUE_PER_LOT; exit_time = future.dt; break

        hour_block = now.dt.strftime("%H:%M")
        profit_by_time[hour_block]["trades"] += 1
        if result == "win": profit_by_time[hour_block]["wins"] += 1
        elif result == "loss": profit_by_time[hour_block]["losses"] += 1

        cumulative_profit += pnl
        balance_history.append((exit_time, cumulative_profit))

        entries.append({
            "entry_time": now.dt.strftime("%Y-%m-%d %H:%M:%S"),
            "exit_time": exit_time.strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": SYMBOL,
            "side": trade_type,
            "entry_price": round(entry_price, 5),
            "tp": round(tp, 5),
            "sl": round(sl, 5),
            "exit_price": round(exit_price, 5),
            "result": result,
            "pnl": pnl
        })

    if entries:
        with open(output_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=entries[0].keys())
            writer.writeheader()
            writer.writerows(entries)

        with open(performance_log, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["HourBlock", "Trades", "Wins", "Losses", "WinRate(%)"])
            for hour in sorted(profit_by_time):
                stats = profit_by_time[hour]
                trades = stats["trades"]
                wins = stats["wins"]
                losses = stats["losses"]
                win_rate = (wins / trades * 100) if trades else 0
                writer.writerow([hour, trades, wins, losses, f"{win_rate:.2f}"])

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
            plt.savefig(equity_curve_png)
            if not silent:
                print(f"Equity curve saved to {equity_curve_png}")

    if not silent:
        print(f"Simulated {len(entries)} trades with TP/SL. Saved to {output_csv}")
        print(f"Hourly profit breakdown saved to {performance_log}")

    return {
        "total_pnl": cumulative_profit,
        "trades": len(entries)
    }

if __name__ == "__main__":
    simulate_strategy()
