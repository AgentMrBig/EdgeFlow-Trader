import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
sys.path.append('.')

from feature_engineer import engineer_features

# ========================= REALISTIC LIVE CONFIG =========================
START_BALANCE = 100.0
RISK_PER_TRADE = 0.02          # 2% risk per trade
MAX_LOT_SIZE = 100.0
MAX_HOLD_CANDLES = 12
COOLDOWN_CANDLES = 15          # 15 minutes pause after 2 consecutive losses

SPREAD_POINTS = 9.0            # From your live screenshots
MARGIN_PER_LOT = 50.0          # 0.01 lot = $0.50 margin

SL_ATR_MULT = 1.1
TP_ATR_MULT = 3.2
TRADE_SESSIONS = "All"

print(f"🚀 Starting Realistic Live Simulation - $100 Start | 2% Risk | 15min pause after 2 losses\n")

df_raw = pd.read_csv('../data/usdjpy_m1.csv')
df = engineer_features(df_raw, lookback=60)

print(f"✅ Engineered {len(df):,} candles\n")

balance = START_BALANCE
equity = [balance]
trades = []
hourly_count = {}
consecutive_losses = 0
cooldown_until = -1

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

    # Cooldown check (15 minutes)
    if i < cooldown_until:
        equity.append(balance)
        continue

    hour_key = current.name.strftime('%Y-%m-%d %H')
    if hourly_count.get(hour_key, 0) >= 20:
        equity.append(balance)
        continue

    # Entry Logic
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

    # Apply spread
    spread = SPREAD_POINTS * 0.0001
    if direction == 'buy':
        entry_price += spread / 2
    else:
        entry_price -= spread / 2

    atr = current['atr_14']
    sl_dist = SL_ATR_MULT * atr
    tp_dist = TP_ATR_MULT * atr

    # Risk & Lot sizing
    risk_amount = balance * RISK_PER_TRADE
    lot_size = max(0.01, min(round(risk_amount / (sl_dist * 100), 2), MAX_LOT_SIZE))

    # Margin check
    required_margin = lot_size * MARGIN_PER_LOT
    if required_margin > balance * 0.8:   # safety buffer
        equity.append(balance)
        continue

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

    # Loss streak & cooldown
    if result == 'loss':
        consecutive_losses += 1
        if consecutive_losses >= 2:
            cooldown_until = i + COOLDOWN_CANDLES
            consecutive_losses = 0
    else:
        consecutive_losses = 0

# ====================== RESULTS ======================
df_trades = pd.DataFrame(trades)
win_rate = len(df_trades[df_trades['result'] == 'win']) / len(df_trades) * 100 if len(df_trades) > 0 else 0

print(f"\n📊 Realistic Live Simulation - $100 Start | 2% Risk | 15min pause after 2 losses")
print(f"Total Trades: {len(df_trades)}")
print(f"Win Rate: {win_rate:.2f}%")
print(f"Final Balance: ${balance:,.2f}")
print(f"Net PnL: ${balance - START_BALANCE:,.2f}")

df_trades.to_csv('edgeflow_trades_realistic_15min_pause.csv', index=False)

plt.figure(figsize=(12, 6))
plt.plot(equity, label='Equity Curve', color='blue')
plt.title('EdgeFlow USD/JPY 1m Scalper - 15min Pause After 2 Losses')
plt.xlabel('Trade Number')
plt.ylabel('Balance ($)')
plt.legend()
plt.grid(True)
plt.savefig('edgeflow_equity_curve_15min_pause.png')
plt.show()

print("💾 Saved results.")
