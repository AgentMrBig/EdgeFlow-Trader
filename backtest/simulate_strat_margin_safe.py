
import pandas as pd
import matplotlib.pyplot as plt

DATA_PATH = "usdjpy_m1.csv"
TRADES_CSV = "simulated_trades.csv"
EQUITY_PNG = "equity_curve_trailing.png"

INITIAL_BALANCE = 100
MAX_OPEN_TRADES = 4
MA_PERIOD = 10
TSL_PIPS = 15
PIP_VALUE = 0.07  # $ per pip for 0.01 lots
PIP_SIZE = 0.01   # pip size for USDJPY
LEVERAGE = 2000
CONTRACT_SIZE = 100000
STOP_OUT_LEVEL = 25  # percent

df = pd.read_csv(DATA_PATH)
df['Timestamp'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Timestamp'].astype(str))
df.set_index('Timestamp', inplace=True)
df['MA'] = df['Close'].rolling(MA_PERIOD).mean()

trades = []
open_trades = []
balance = INITIAL_BALANCE

for i in range(MA_PERIOD + 2, len(df)):
    now = df.iloc[i]
    prev = df.iloc[i - 1]
    prev2 = df.iloc[i - 2]
    time = df.index[i]
    price = now['Close']

    # update floating PnL, margin, equity
    floating_pnl = 0
    margin_used = 0
    still_open = []

    for trade in open_trades:
        high = max(trade['highest_price'], now['High'])
        tsl = high - TSL_PIPS * PIP_SIZE
        trade['highest_price'] = high

        if price <= tsl:
            pnl_pips = (trade['entry_price'] - price) / PIP_SIZE
            pnl = round(pnl_pips * PIP_VALUE, 2)
            trades.append({
                'entry_time': trade['entry_time'],
                'exit_time': time,
                'entry_price': trade['entry_price'],
                'exit_price': price,
                'pnl': pnl
            })
            balance += pnl
        else:
            trade['pnl'] = (trade['entry_price'] - price) * (CONTRACT_SIZE * 0.01) / 10000
            floating_pnl += trade['pnl']
            margin_used += (0.01 * CONTRACT_SIZE) / LEVERAGE
            still_open.append(trade)

    open_trades = still_open
    equity = balance + floating_pnl
    margin_level = (equity / margin_used) * 100 if margin_used > 0 else float('inf')
    free_margin = equity - margin_used

    # margin stop-out
    if margin_level < STOP_OUT_LEVEL:
        balance = equity
        open_trades = []
        continue

    # avoid duplicate entries per candle
    if any(trade['entry_time'] == time for trade in open_trades):
        continue

    broke_below_ma = prev2['Close'] > prev2['MA'] and prev['Close'] < prev['MA']
    retested_ma = prev['High'] >= prev['MA']
    broke_prev_lows = now['Low'] < min(prev['Low'], prev2['Low'])

    if broke_below_ma and retested_ma and broke_prev_lows and len(open_trades) < MAX_OPEN_TRADES:
        margin_required = (0.01 * CONTRACT_SIZE) / LEVERAGE
        if free_margin >= margin_required:
            entry = price
            trade = {
                'entry_time': time,
                'entry_price': entry,
                'highest_price': entry,
                'pnl': 0
            }
            open_trades.append(trade)

df_trades = pd.DataFrame(trades)
if not df_trades.empty:
    df_trades['Timestamp'] = pd.to_datetime(df_trades['exit_time'])
    df_trades.set_index('Timestamp', inplace=True)
    df_trades['balance'] = INITIAL_BALANCE + df_trades['pnl'].cumsum()
    df_trades.to_csv(TRADES_CSV)

    plt.figure(figsize=(10, 5))
    plt.plot(df_trades['balance'], label='Equity Curve')
    plt.title('Equity Curve with Trailing Stop + Margin Logic')
    plt.xlabel('Time')
    plt.ylabel('Balance')
    plt.legend()
    plt.tight_layout()
    plt.savefig(EQUITY_PNG)
    plt.close()

print(f"Simulation complete. Trades executed: {len(trades)}")
