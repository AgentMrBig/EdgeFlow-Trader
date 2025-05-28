"""
Analyze simulated trades for win/loss conditions, timing, and duration insights.
"""
import pandas as pd
from datetime import datetime
import os

# File paths
TRADE_FILE = "simulated_trades.csv"
OUTPUT_ANALYSIS_FILE = "trade_analysis.csv"

# Load trade data
def load_trades(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")
    df = pd.read_csv(path, parse_dates=['entry_time', 'exit_time'])
    return df

# Add outcome + duration
def enrich_trades(df):
    df['win'] = df['pnl'] > 0
    df['duration_min'] = (df['exit_time'] - df['entry_time']).dt.total_seconds() / 60
    df['hour'] = df['entry_time'].dt.hour
    df['day_of_week'] = df['entry_time'].dt.day_name()
    return df

# Aggregate performance by time
def time_analysis(df):
    by_hour = df.groupby('hour')['win'].agg(['count', 'sum'])
    by_hour['win_rate'] = by_hour['sum'] / by_hour['count'] * 100

    by_day = df.groupby('day_of_week')['win'].agg(['count', 'sum'])
    by_day['win_rate'] = by_day['sum'] / by_day['count'] * 100

    return by_hour, by_day

# Save enriched data
def save_analysis(df):
    df.to_csv(OUTPUT_ANALYSIS_FILE, index=False)
    print(f"\n✅ Saved enriched trade data to {OUTPUT_ANALYSIS_FILE}")

# Main pipeline
def main():
    df = load_trades(TRADE_FILE)
    df = enrich_trades(df)

    by_hour, by_day = time_analysis(df)

    print("\n📊 Win Rate by Hour:")
    print(by_hour.round(2))

    print("\n📅 Win Rate by Day of Week:")
    print(by_day.round(2))

    save_analysis(df)

if __name__ == "__main__":
    main()
