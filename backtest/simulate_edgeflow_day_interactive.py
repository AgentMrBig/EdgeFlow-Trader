import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
sys.path.append('.')

from feature_engineer import engineer_features

print("🚀 First Half-Day Interactive Test - Clean Visuals\n")

# ========================= CONFIG =========================
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

# Load data and take first half of the most recent day
df_raw = pd.read_csv('../data/usdjpy_m1.csv')
df_raw['timestamp'] = pd.to_datetime(df_raw['Date'].astype(str) + ' ' + df_raw['Timestamp'])
df_raw = df_raw.sort_values('timestamp')

# First half of the most recent day (~12 hours)
half_day = df_raw.iloc[-720:].reset_index(drop=True)   # ~12 hours

df = engineer_features(half_day, lookback=60)

print(f"✅ Engineered {len(df):,} candles (first half day)\n")

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
    equity.append(balance)

    trades.append({
        'timestamp': current.name,
        'direction': direction,
        'entry': entry_price,
        'exit': exit_price,
        'lot_size': lot_size,
        'result': result,
        'profit': profit
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

print(f"\n📊 First Half-Day Interactive Test Results")
print(f"Total Trades: {len(df_trades)}")
print(f"Win Rate: {win_rate:.2f}%")
print(f"Final Balance: ${balance:,.2f}")
print(f"Net PnL: ${balance - START_BALANCE:,.2f}")

# ====================== CLEAN INTERACTIVE CHART ======================
chart_df = half_day.copy()
chart_df = chart_df.rename(columns={'Open':'open', 'High':'high', 'Low':'low', 'Close':'close'})
chart_df.set_index('timestamp', inplace=True)

fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25])

fig.add_trace(go.Candlestick(x=chart_df.index,
                             open=chart_df['open'],
                             high=chart_df['high'],
                             low=chart_df['low'],
                             close=chart_df['close'],
                             name='USD/JPY'), row=1, col=1)

for trade in trades:
    color = 'lime' if trade['result'] == 'win' else 'red'
    symbol = 'triangle-up' if trade['direction'] == 'buy' else 'triangle-down'
    
    # Entry marker with hover info
    fig.add_trace(go.Scatter(x=[trade['timestamp']], y=[trade['entry']],
                             mode='markers',
                             marker=dict(size=14, symbol=symbol, color=color, line=dict(width=2, color='white')),
                             name=f"{trade['direction'].upper()} {trade['lot_size']:.2f} lot",
                             hovertemplate=f"Entry: {trade['direction'].upper()} {trade['lot_size']:.2f} lot<br>"
                                           f"Price: {trade['entry']:.4f}<br>"
                                           f"Time: %{{x}}"), row=1, col=1)
    
    # Dotted exit line
    fig.add_trace(go.Scatter(x=[trade['timestamp'], trade['timestamp']], 
                             y=[trade['entry'], trade['exit']],
                             mode='lines', line=dict(dash='dash', color=color, width=1.5),
                             name='Exit', hoverinfo='skip'), row=1, col=1)

fig.update_layout(title='USD/JPY 1m - First Half Day Interactive Test (Zoom + Scroll)',
                  xaxis_title='Time',
                  yaxis_title='Price',
                  height=900,
                  template='plotly_dark',
                  showlegend=False)

fig.write_html("1day_interactive_test.html")
print("\n💾 Saved: 1day_interactive_test.html")
print("Open this file in your browser → zoom, scroll, and hover over markers for details.")
print("Done.")
