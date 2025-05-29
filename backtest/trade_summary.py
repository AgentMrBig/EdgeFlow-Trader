
import pandas as pd
from datetime import timedelta
from dateutil.relativedelta import relativedelta

def format_duration(start, end):
    rd = relativedelta(end, start)
    parts = []
    if rd.years:
        parts.append(f"{rd.years} year{'s' if rd.years > 1 else ''}")
    if rd.months:
        parts.append(f"{rd.months} month{'s' if rd.months > 1 else ''}")
    if rd.days:
        parts.append(f"{rd.days} day{'s' if rd.days > 1 else ''}")
    return ', '.join(parts)

def summarize_trades(csv_path='simulated_trades.csv'):
    df = pd.read_csv(csv_path, parse_dates=['entry_time', 'exit_time'])

    if df.empty:
        print("No trades found.")
        return

    start_date = df['entry_time'].min().date()
    end_date = df['entry_time'].max().date()
    duration = format_duration(start_date, end_date)
    total_trades = len(df)
    df['date'] = df['entry_time'].dt.date
    df['hour'] = df['entry_time'].dt.hour
    df['week'] = df['entry_time'].dt.to_period('W').apply(lambda r: r.start_time.date())

    total_days_span = (end_date - start_date).days + 1
    total_trading_days = df['date'].nunique()
    total_weeks = len(df['week'].unique())

    avg_per_day = total_trades / total_trading_days
    avg_per_week = total_trades / total_weeks
    avg_per_hour = df.groupby('hour').size().mean()

    avg_win = df[df['pnl'] > 0]['pnl'].mean()
    avg_loss = df[df['pnl'] < 0]['pnl'].mean()
    biggest_win = df['pnl'].max()
    biggest_loss = df['pnl'].min()

    print("📅 Trade Summary Report")
    print(f"Date Range        : {start_date} → {end_date}")
    print(f"Trade Period      : {duration}")
    print(f"Total Trades      : {total_trades}")
    print(f"Active Trading Days : {total_trading_days}")
    print(f"Total Calendar Days : {total_days_span}")
    print(f"Total Weeks       : {total_weeks}")
    print(f"Average/Day       : {avg_per_day:.2f}")
    print(f"Average/Week      : {avg_per_week:.2f}")
    print(f"Average/Hour      : {avg_per_hour:.2f}")
    print(f"Average Win       : {avg_win:.2f}")
    print(f"Average Loss      : {avg_loss:.2f}")
    print(f"Biggest Win       : {biggest_win:.2f}")
    print(f"Biggest Loss      : {biggest_loss:.2f}")

    trades_by_day = df['date'].value_counts().sort_index()
    print("\n📈 Trades Per Day")
    print(trades_by_day)

    trades_by_week = df['week'].value_counts().sort_index()
    print("\n📈 Trades Per Week")
    print(trades_by_week)

    trades_by_hour = df['hour'].value_counts().sort_index()
    print("\n📈 Trades Per Hour")
    print(trades_by_hour)

    print("\n🏆 Top 10 Wins")
    print(df.sort_values(by='pnl', ascending=False).head(10)[['entry_time', 'pnl']])

    print("\n💥 Top 10 Losses")
    print(df.sort_values(by='pnl').head(10)[['entry_time', 'pnl']])

if __name__ == "__main__":
    summarize_trades()
