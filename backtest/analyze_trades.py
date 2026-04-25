import pandas as pd

# Load the latest trade log
df = pd.read_csv('edgeflow_trades_all_sessions_100start.csv')

print("=== TRADE ANALYSIS ===")
print(f"Total Trades: {len(df)}")
print(f"Win Rate: {df['result'].value_counts(normalize=True).get('win', 0)*100:.2f}%")
print(f"Final Balance: ${df['balance'].iloc[-1]:,.2f}\n")

# Lot Size Analysis
print("=== LOT SIZE ANALYSIS ===")
print(f"Average lot size: {df['lot_size'].mean():.4f}")
print(f"Min lot size: {df['lot_size'].min()}")
print(f"Max lot size: {df['lot_size'].max()}")
print("\nLot size distribution:")
print(df['lot_size'].value_counts().sort_index().head(10))

# Hold Duration (using index difference as proxy since exit_time may not exist)
df = df.reset_index()
df['hold_duration'] = df['index'].diff().fillna(1).astype(int)  # approximate candles held

print("\n=== HOLD DURATION ANALYSIS ===")
print("Average hold duration (candles):")
print(df.groupby('result')['hold_duration'].mean())

print("\nWin rate by hold duration bins:")
duration_bins = pd.cut(df['hold_duration'], bins=range(0, 16, 2))
win_rate_by_hold = df.groupby(duration_bins)['result'].value_counts(normalize=True).unstack().get('win', 0) * 100
print(win_rate_by_hold)

print("\nDone.")
