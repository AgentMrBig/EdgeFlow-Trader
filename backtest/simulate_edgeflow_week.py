import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
sys.path.append('.')

from feature_engineer import engineer_features

# ========================= QUICK TEST CONFIG (1 WEEK) =========================
START_BALANCE = 100.0
RISK_PER_TRADE = 0.02
MAX_LOT_SIZE = 100.0
MAX_HOLD_CANDLES = 12
COOLDOWN_CANDLES = 15          # 15 minutes pause after 2 losses

SPREAD_POINTS = 9.0
MARGIN_PER_LOT = 50.0

SL_ATR_MULT = 1.1
TP_ATR_MULT = 3.2
TRADE_SESSIONS = "All"

print("🚀 Quick Test - Last 1 Week Only | 2% Risk | 15min pause after 2 losses\n")

# Load full data then take last 7 days
df_raw = pd.read_csv('../data/usdjpy_m1.csv')
df_raw['timestamp'] = pd.to_datetime(df_raw['Date'].astype(str) + ' ' + df_raw['Timestamp'])
df_raw = df_raw.sort_values('timestamp')

# Take only the most recent 7 days
one_week = df_raw.iloc[-10080:]   # ~7 days * 1440 minutes
print(f"Using last {len(one_week)} candles (~1 week) for fast testing\n")

df = engineer_features(one_week.reset_index(drop=True), lookback=60)

print(f"✅ Engineered {len(df):,} candles for testing\n")

# ... [rest of the simulation code remains the same - I'll keep it short here]

balance = START_BALANCE
equity = [balance]
trades = []
hourly_count = {}
consecutive_losses = 0
cooldown_until = -1

for i in range(60, len(df) - MAX_HOLD_CANDLES):
    current = df.iloc[i]
    session = current['session']

    if TRADE_SESSIONS != "All" and session != TRADE_SESSIONS:
        equity.append(balance)
        continue

    if i < cooldown_until:
        equity.append(balance)
        continue

    hour_key = current.name.strftime('%Y-%m-%d %H')
    if hourly_count.get(hour_key, 0) >= 20:
        equity.append(balance)
        continue

    # Entry Logic (same as before)
    long_signal = (current['htf_bias'] == 1 and current['above_ma9'] == 1 and 
                   current['ma9_slope'] > 0 and current['stoch_k'] < 75 and
                   current['bb_width'] > df['bb_width'].rolling(20).mean().iloc[i])

    short_signal = (current['htf_bias'] == -1 and current['above_ma9'] == 0 and 
                    current['ma9_slope'] < 0 and current['stoch_k'] > 25 and
                    current['bb_width'] > df['bb_width'].rolling(20).mean().iloc[i])

    if not (long_signal or short_signal):
        equity.append(balance)
        continue

    direction = 'buy' if long_signal else 'sell'
    mid_price = current['Close']
    spread = SPREAD_POINTS * 0.0001
    entry_price = mid_price + (spread / 2) if direction == 'buy' else mid_price - (spread / 2)

    atr = current['atr_14']
    sl_dist = SL_ATR_MULT * atr
    tp_dist = TP_ATR_MULT * atr

    risk_amount = balance * RISK_PER_TRADE
    lot_size = max(0.01, min(round(risk_amount / (sl_dist * 100), 2), MAX_LOT_SIZE))

    # Margin check
    if lot_size * MARGIN_PER_LOT > balance * 0.6:
        equity.append(balance)
        continue

    # Simulate exit (with spread on exit too)
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
    equity.append(balance)

    trades.append({'timestamp': current.name, 'direction': direction, 'lot_size': lot_size, 
                   'result': result, 'profit': round(profit, 2), 'balance': round(balance, 2)})

    hourly_count[hour_key] = hourly_count.get(hour_key, 0) + 1

    if result == 'loss':
        consecutive_losses += 1
        if consecutive_losses >= 2:
            cooldown_until = i + COOLDOWN_CANDLES
            consecutive_losses = 0
    else:
        consecutive_losses = 0

df_trades = pd.DataFrame(trades)
win_rate = len(df_trades[df_trades['result'] == 'win']) / len(df_trades) * 100 if len(df_trades) > 0 else 0

print(f"\n📊 Quick 1-Week Test Results")
print(f"Total Trades: {len(df_trades)}")
print(f"Win Rate: {win_rate:.2f}%")
print(f"Final Balance: ${balance:,.2f}")
print(f"Net PnL: ${balance - START_BALANCE:,.2f}")

plt.figure(figsize=(12, 6))
plt.plot(equity, label='Equity Curve', color='blue')
plt.title('Quick 1-Week Test - 15min Pause After 2 Losses')
plt.xlabel('Trade Number')
plt.ylabel('Balance ($)')
plt.legend()
plt.grid(True)
plt.show()

print("Done.")
