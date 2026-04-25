import pandas as pd
import numpy as np
import json
import mplfinance as mpf
import sys
sys.path.append('.')

from feature_engineer import engineer_features

# ========================= 1-DAY FAST VISUAL TEST =========================
START_BALANCE = 100.0
RISK_PER_TRADE = 0.02
MAX_LOT_SIZE = 100.0
MAX_HOLD_CANDLES = 12
COOLDOWN_CANDLES = 15
SPREAD_POINTS = 9.0
MARGIN_PER_LOT = 50.0
SL_ATR_MULT = 1.1
TP_ATR_MULT = 3.2
TRADE_SESSIONS = "All"

print("🚀 1-Day Visual Test - Realistic Live Simulation\n")

df_raw = pd.read_csv('./data/usdjpy_m1.csv')
df_raw['timestamp'] = pd.to_datetime(df_raw['Date'].astype(str) + ' ' + df_raw['Timestamp'])
df_raw = df_raw.sort_values('timestamp')
one_day = df_raw.iloc[-1440:].reset_index(drop=True)

df = engineer_features(one_day, lookback=60)
print(f"✅ Engineered {len(df):,} candles for 1-day test\n")

balance = START_BALANCE
equity = [balance]
trades = []
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

    long_signal = (
        current['htf_bias'] == 1 and current['above_ma9'] == 1 and
        current['ma9_slope'] > 0 and current['stoch_k'] < 75 and
        current['bb_width'] > df['bb_width'].rolling(20).mean().iloc[i]
    )
    short_signal = (
        current['htf_bias'] == -1 and current['above_ma9'] == 0 and
        current['ma9_slope'] < 0 and current['stoch_k'] > 25 and
        current['bb_width'] > df['bb_width'].rolling(20).mean().iloc[i]
    )

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

    if lot_size * MARGIN_PER_LOT > balance * 0.6:
        equity.append(balance)
        continue

    exit_price = None
    result = None
    exit_idx = None
    for j in range(1, MAX_HOLD_CANDLES + 1):
        fut = df.iloc[i + j]
        if direction == 'buy':
            if fut['High'] - entry_price >= tp_dist:
                exit_price = entry_price + tp_dist - (spread / 2)
                result = 'win'
                exit_idx = i + j
                break
            if entry_price - fut['Low'] >= sl_dist:
                exit_price = entry_price - sl_dist + (spread / 2)
                result = 'loss'
                exit_idx = i + j
                break
        else:
            if entry_price - fut['Low'] >= tp_dist:
                exit_price = entry_price - tp_dist + (spread / 2)
                result = 'win'
                exit_idx = i + j
                break
            if fut['High'] - entry_price >= sl_dist:
                exit_price = entry_price + sl_dist - (spread / 2)
                result = 'loss'
                exit_idx = i + j
                break

    if exit_price is None:
        final = df.iloc[i + MAX_HOLD_CANDLES]
        exit_price = final['Close']
        exit_idx = i + MAX_HOLD_CANDLES
        result = 'win' if (direction == 'buy' and exit_price > entry_price) or (direction == 'sell' and exit_price < entry_price) else 'loss'

    pip_diff = (exit_price - entry_price) if direction == 'buy' else (entry_price - exit_price)
    profit = pip_diff * lot_size * 1000
    balance += profit
    equity.append(balance)

    trades.append({
        'timestamp': str(one_day.iloc[i]['timestamp']),
        'direction': direction,
        'entry': round(entry_price, 5),
        'exit': round(exit_price, 5),
        'lot_size': lot_size,
        'result': result,
        'profit': round(profit, 2),
        'exit_timestamp': str(one_day.iloc[exit_idx]['timestamp'])
    })

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

print(f"\n📊 1-Day Visual Test Results")
print(f"Total Trades: {len(df_trades)}")
print(f"Win Rate: {win_rate:.2f}%")
print(f"Final Balance: ${balance:,.2f}")
print(f"Net PnL: ${balance - START_BALANCE:,.2f}")

# ====================== EXPORT TRADES FOR INTERACTIVE CHART ======================
with open('static/trades.json', 'w') as f:
    json.dump(trades, f, indent=2)
print("✅ Exported trades to static/trades.json (ready for interactive chart)")

# ====================== MPLFINANCE PNG (optional) ======================
chart_df = one_day.copy()
chart_df = chart_df.rename(columns={'Open':'open', 'High':'high', 'Low':'low', 'Close':'close'})
chart_df.set_index('timestamp', inplace=True)

add_plots = []
for trade in trades:
    entry_time = pd.to_datetime(trade['timestamp'])
    entry_price = trade['entry']
    exit_time = pd.to_datetime(trade['exit_timestamp'])
    exit_price = trade['exit']
    color = 'green' if trade['result'] == 'win' else 'red'

    add_plots.append(mpf.make_addplot([entry_price if t == entry_time else np.nan for t in chart_df.index],
                                      type='scatter', markersize=80, marker='^', color=color))
    line = [entry_price if t == entry_time else exit_price if t == exit_time else np.nan for t in chart_df.index]
    add_plots.append(mpf.make_addplot(line, type='line', linestyle='dotted', color=color, width=1.5))

mpf.plot(chart_df, type='candle', style='yahoo', addplot=add_plots,
         title='USD/JPY 1m - 1 Day Test with Trades',
         ylabel='Price', figsize=(14, 8), savefig='1day_visual_test.png')

print("💾 Saved 1day_visual_test.png")
print("Now refresh your interactive chart — it will load the same trades!")
