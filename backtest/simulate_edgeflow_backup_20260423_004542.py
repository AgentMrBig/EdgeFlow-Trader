import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
sys.path.append('.')

from feature_engineer import engineer_features

# ========================= REALISTIC CONFIG =========================
START_BALANCE = 100.0
RISK_PER_TRADE = 0.01
MAX_TRADES_PER_HOUR = 4
MAX_HOLD_CANDLES = 12
MAX_LOT_SIZE = 100.0          # Updated per your request

SL_ATR_MULT = 1.1
TP_ATR_MULT = 3.2

TRADE_SESSIONS = "All"

print(f"🚀 Starting EdgeFlow USD/JPY 1m Scalper - $100 Start | Max Lots: {MAX_LOT_SIZE}\n")

df_raw = pd.read_csv('../data/usdjpy_m1.csv')
df = engineer_features(df_raw, lookback=60)

print(f"✅ Engineered {len(df):,} candles\n")

balance = START_BALANCE
equity = [balance]
trades = []
hourly_count = {}

for i in range(60, len(df) - MAX_HOLD_CANDLES):
    current = df.iloc[i]
    session = current['session']

    if TRADE_SESSIONS != "All":
        if isinstance(TRADE_SESSIONS, list):
            if session not in TRADE_SESSIONS:
                equity.append(balance)
                continue
        elif session != TRADE_SESSIONS:
            equity.append(balance)
            continue

    hour_key = current.name.strftime('%Y-%m-%d %H')
    if hourly_count.get(hour_key, 0) >= MAX_TRADES_PER_HOUR:
        equity.append(balance)
        continue

    long_signal = (
        current['htf_bias'] == 1 and
        current['above_ma9'] == 1 and
        current['ma9_slope'] > 0 and
        current['stoch_k'] < 75 and
        current['bb_width'] > df['bb_width'].rolling(20).mean().iloc[i]
    )

    short_signal = (
        current['htf_bias'] == -1 and
        current['above_ma9'] == 0 and
        current['ma9_slope'] < 0 and
        current['stoch_k'] > 25 and
        current['bb_width'] > df['bb_width'].rolling(20).mean().iloc[i]
    )

    if not (long_signal or short_signal):
        equity.append(balance)
        continue

    direction = 'buy' if long_signal else 'sell'
    entry_price = current['Close']
    atr = current['atr_14']

    sl_dist = SL_ATR_MULT * atr
    tp_dist = TP_ATR_MULT * atr

    risk_amount = balance * RISK_PER_TRADE
    lot_size = max(0.01, min(round(risk_amount / (sl_dist * 100), 2), MAX_LOT_SIZE))

    # Simulate exit
    exit_price = None
    result = None
    for j in range(1, MAX_HOLD_CANDLES + 1):
        fut = df.iloc[i + j]
        if direction == 'buy':
            if fut['High'] - entry_price >= tp_dist:
                exit_price = entry_price + tp_dist
                result = 'win'
                break
            if entry_price - fut['Low'] >= sl_dist:
                exit_price = entry_price - sl_dist
                result = 'loss'
                break
        else:
            if entry_price - fut['Low'] >= tp_dist:
                exit_price = entry_price - tp_dist
                result = 'win'
                break
            if fut['High'] - entry_price >= sl_dist:
                exit_price = entry_price + sl_dist
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

    trades.append({
        'timestamp': current.name,
        'direction': direction,
        'entry': round(entry_price, 5),
        'exit': round(exit_price, 5),
        'lot_size': lot_size,
        'result': result,
        'profit': round(profit, 2),
        'balance': round(balance, 2),
        'session': session
    })

    hourly_count[hour_key] = hourly_count.get(hour_key, 0) + 1

# ====================== RESULTS ======================
df_trades = pd.DataFrame(trades)
win_rate = len(df_trades[df_trades['result'] == 'win']) / len(df_trades) * 100 if len(df_trades) > 0 else 0

print(f"\n📊 Simulation Results - $100 Start | Sessions: {TRADE_SESSIONS}")
print(f"Total Trades: {len(df_trades)}")
print(f"Win Rate: {win_rate:.2f}%")
print(f"Final Balance: ${balance:,.2f}")
print(f"Net PnL: ${balance - START_BALANCE:,.2f}")

df_trades.to_csv('edgeflow_trades_100start_all.csv', index=False)

plt.figure(figsize=(12, 6))
plt.plot(equity, label='Equity Curve', color='blue')
plt.title('EdgeFlow USD/JPY 1m Scalper - $100 Start | All Sessions')
plt.xlabel('Trade Number')
plt.ylabel('Balance ($)')
plt.legend()
plt.grid(True)
plt.savefig('edgeflow_equity_curve_100start_all.png')
plt.show()

print("💾 Saved results.")
