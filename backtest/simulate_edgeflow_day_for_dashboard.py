import pandas as pd
import numpy as np
import json
import sys
sys.path.append('.')

from feature_engineer import engineer_features

print("🚀 Generating data for Dashboard (1 Day)\n")

# Config
START_BALANCE = 100.0
RISK_PER_TRADE = 0.02
MAX_LOT_SIZE = 100.0
MAX_HOLD_CANDLES = 12
COOLDOWN_CANDLES = 15
SPREAD_POINTS = 9.0

df_raw = pd.read_csv('../data/usdjpy_m1.csv')
df_raw['timestamp'] = pd.to_datetime(df_raw['Date'].astype(str) + ' ' + df_raw['Timestamp'])
df_raw = df_raw.sort_values('timestamp')
one_day = df_raw.iloc[-1440:].reset_index(drop=True)

df = engineer_features(one_day, lookback=60)

balance = START_BALANCE
trades = []
consecutive_losses = 0
cooldown_until = -1

for i in range(60, len(df) - MAX_HOLD_CANDLES):
    current = df.iloc[i]

    if i < cooldown_until:
        continue

    long_signal = (current['htf_bias'] == 1 and current['above_ma9'] == 1 and
                   current['ma9_slope'] > 0 and current['stoch_k'] < 75 and
                   current['bb_width'] > df['bb_width'].rolling(20).mean().iloc[i])

    short_signal = (current['htf_bias'] == -1 and current['above_ma9'] == 0 and
                    current['ma9_slope'] < 0 and current['stoch_k'] > 25 and
                    current['bb_width'] > df['bb_width'].rolling(20).mean().iloc[i])

    if not (long_signal or short_signal):
        continue

    direction = 'buy' if long_signal else 'sell'
    mid_price = current['Close']
    spread = SPREAD_POINTS * 0.0001
    entry_price = mid_price + (spread / 2) if direction == 'buy' else mid_price - (spread / 2)

    atr = current['atr_14']
    sl_dist = 1.1 * atr
    tp_dist = 3.2 * atr

    risk_amount = balance * RISK_PER_TRADE
    lot_size = max(0.01, min(round(risk_amount / (sl_dist * 100), 2), MAX_LOT_SIZE))

    # Simulate exit
    exit_price = None
    result = None
    for j in range(1, MAX_HOLD_CANDLES + 1):
        fut = df.iloc[i + j]
        if direction == 'buy':
            if fut['High'] - entry_price >= tp_dist:
                exit_price = entry_price + tp_dist - (spread / 2)
                result = 'win'
                break
            if entry_price - fut['Low'] >= sl_dist:
                exit_price = entry_price - sl_dist + (spread / 2)
                result = 'loss'
                break
        else:
            if entry_price - fut['Low'] >= tp_dist:
                exit_price = entry_price - tp_dist + (spread / 2)
                result = 'win'
                break
            if fut['High'] - entry_price >= sl_dist:
                exit_price = entry_price + sl_dist - (spread / 2)
                result = 'loss'
                break

    if exit_price is None:
        final = df.iloc[i + MAX_HOLD_CANDLES]
        exit_price = final['Close']
        result = 'win' if (direction == 'buy' and exit_price > entry_price) or (direction == 'sell' and exit_price < entry_price) else 'loss'

    pip_diff = (exit_price - entry_price) if direction == 'buy' else (entry_price - exit_price)
    profit = pip_diff * lot_size * 1000
    balance += profit

    trades.append({
        "timestamp": current.name.strftime("%Y-%m-%d %H:%M:%S"),
        "direction": direction,
        "entry": round(entry_price, 5),
        "exit": round(exit_price, 5),
        "lot_size": lot_size,
        "result": result,
        "profit": round(profit, 2)
    })

    if result == 'loss':
        consecutive_losses += 1
        if consecutive_losses >= 2:
            cooldown_until = i + COOLDOWN_CANDLES
            consecutive_losses = 0
    else:
        consecutive_losses = 0

# Save for dashboard
with open('../webapp/static/equity_data.json', 'w') as f:
    json.dump(trades, f, indent=2)

print(f"✅ Exported {len(trades)} trades to equity_data.json")
print("Ready for dashboard.")
