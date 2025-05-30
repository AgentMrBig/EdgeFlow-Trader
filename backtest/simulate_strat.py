
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta
import sys
import numpy as np

DATA_PATH = "usdjpy_m1.csv"
TRADES_CSV = "simulated_trades.csv"
EQUITY_PNG = "equity_curve_trailing.png"

INITIAL_BALANCE = 100
MAX_OPEN_TRADES = 4
MA_PERIOD = 10
TSL_PIPS = 15
BREAKEVEN_TRIGGER_PIPS = 5
LOSS_EXIT_AFTER_CANDLES = 15
SR_PROXIMITY_PIPS = 5

PIP_VALUE = 0.07
PIP_SIZE = 0.01
LEVERAGE = 2000
CONTRACT_SIZE = 100000
STOP_OUT_LEVEL = 25

# Load M1 data
df = pd.read_csv(DATA_PATH)
df['Timestamp'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Timestamp'].astype(str))
df.set_index('Timestamp', inplace=True)
df['MA'] = df['Close'].rolling(MA_PERIOD).mean()

# Derive 5-min data
df_5min = df['Close'].resample('5min').ohlc()
rolling_high = df_5min['high'].rolling(window=10).max()
rolling_low = df_5min['low'].rolling(window=10).min()
sr_levels = pd.concat([rolling_high, rolling_low]).dropna().unique()

def is_near_sr(price):
    return any(abs(price - sr) <= SR_PROXIMITY_PIPS * PIP_SIZE for sr in sr_levels)

trades = []
open_trades = []
balance = INITIAL_BALANCE

for i in range(MA_PERIOD + 2, len(df)):
    now = df.iloc[i]
    prev = df.iloc[i - 1]
    prev2 = df.iloc[i - 2]
    time = df.index[i]
    price = now['Close']

    floating_pnl = 0
    margin_used = 0
    still_open = []

    for trade in open_trades:
        trade['bars_open'] += 1
        unrealized_pips = (trade['entry_price'] - price) / PIP_SIZE
        trade['pnl'] = unrealized_pips * PIP_VALUE
        floating_pnl += trade['pnl']
        margin_used += (0.01 * CONTRACT_SIZE) / LEVERAGE

        reached_breakeven = (trade['entry_price'] - price) >= BREAKEVEN_TRIGGER_PIPS * PIP_SIZE
        if reached_breakeven and not trade['trailing_active']:
            trade['trailing_active'] = True
            trade['highest_price'] = max(trade['highest_price'], price)

        if trade['trailing_active']:
            trade['highest_price'] = max(trade['highest_price'], price)
            tsl = trade['highest_price'] - TSL_PIPS * PIP_SIZE
            if price <= tsl:
                pnl = round(trade['pnl'], 2)
                trades.append({
                    'entry_time': trade['entry_time'],
                    'exit_time': time,
                    'entry_price': trade['entry_price'],
                    'exit_price': price,
                    'pnl': pnl
                })
                balance += pnl
                continue

        if trade['pnl'] < 0 and trade['bars_open'] >= LOSS_EXIT_AFTER_CANDLES:
            if not is_near_sr(price):
                pnl = round(trade['pnl'], 2)
                trades.append({
                    'entry_time': trade['entry_time'],
                    'exit_time': time,
                    'entry_price': trade['entry_price'],
                    'exit_price': price,
                    'pnl': pnl
                })
                balance += pnl
                continue

        still_open.append(trade)

    open_trades = still_open
    equity = balance + floating_pnl
    margin_level = (equity / margin_used) * 100 if margin_used > 0 else float('inf')
    free_margin = equity - margin_used

    if margin_level < STOP_OUT_LEVEL:
        print(f"💥 Margin call triggered at {time}. Account busted. Final equity: ${equity:.2f}")
        break

    if any(trade['entry_time'] == time for trade in open_trades):
        continue

    broke_below_ma = prev2['Close'] > prev2['MA'] and prev['Close'] < prev['MA']
    retested_ma = prev['High'] >= prev['MA']
    broke_prev_lows = now['Low'] < min(prev['Low'], prev2['Low'])

    if broke_below_ma and retested_ma and broke_prev_lows and len(open_trades) < MAX_OPEN_TRADES:
        margin_required = (0.01 * CONTRACT_SIZE) / LEVERAGE
        if free_margin >= margin_required:
            entry = price
            open_trades.append({
                'entry_time': time,
                'entry_price': entry,
                'highest_price': entry,
                'pnl': 0,
                'bars_open': 0,
                'trailing_active': False
            })

df_trades = pd.DataFrame(trades)
if not df_trades.empty:
    df_trades['Timestamp'] = pd.to_datetime(df_trades['exit_time'])
    df_trades.set_index('Timestamp', inplace=True)
    df_trades['balance'] = INITIAL_BALANCE + df_trades['pnl'].cumsum()
    df_trades.to_csv(TRADES_CSV)

    plt.figure(figsize=(10, 5))
    plt.plot(df_trades['balance'], label='Equity Curve')
    plt.title('Equity Curve with Smart Exits and Margin Enforcement')
    plt.xlabel('Time')
    plt.ylabel('Balance')
    plt.legend()
    plt.tight_layout()
    plt.savefig(EQUITY_PNG)
    plt.close()

print(f"Simulation complete. Trades executed: {len(trades)}")
