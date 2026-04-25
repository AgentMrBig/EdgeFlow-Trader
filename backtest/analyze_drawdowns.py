import pandas as pd
import numpy as np

FILENAME = 'edgeflow_trades_100start_all.csv'   # Change only if your latest file has a different name

print(f"Loading {FILENAME} ...")
df = pd.read_csv(FILENAME)

print(f"Total trades loaded: {len(df)}")
print(f"Final balance: ${df['balance'].iloc[-1]:,.2f}\n")

equity = df['balance'].values

def find_drawdowns(equity):
    drawdowns = []
    peak = equity[0]
    peak_idx = 0
    
    for i in range(1, len(equity)):
        if equity[i] > peak:
            peak = equity[i]
            peak_idx = i
        else:
            trough = equity[i]
            trough_idx = i
            dd_amount = peak - trough
            dd_percent = (dd_amount / peak) * 100 if peak > 0 else 0
            
            if dd_amount > 500:   # Only record meaningful drawdowns (>$500)
                drawdowns.append({
                    'start_trade': peak_idx,
                    'end_trade': trough_idx,
                    'start_balance': peak,
                    'end_balance': trough,
                    'dd_amount': dd_amount,
                    'dd_percent': dd_percent,
                    'trades_in_dd': trough_idx - peak_idx + 1
                })
                peak = equity[i]
                peak_idx = i
    return drawdowns

drawdowns = find_drawdowns(equity)

# Save full analysis to file
with open('drawdown_analysis.txt', 'w', encoding='utf-8') as f:
    f.write("=== DRAWDOWN ANALYSIS REPORT ===\n\n")
    f.write(f"Total Trades: {len(df)}\n")
    f.write(f"Final Balance: ${df['balance'].iloc[-1]:,.2f}\n\n")
    f.write(f"Found {len(drawdowns)} significant drawdown periods\n\n")
    
    for idx, dd in enumerate(drawdowns):
        start = dd['start_trade']
        end = dd['end_trade']
        segment = df.iloc[start:end+1]
        
        wins = (segment['result'] == 'win').sum()
        total = len(segment)
        win_rate = (wins / total * 100) if total > 0 else 0
        
        # Loss streak
        results = segment['result'].values
        current_streak = 0
        max_streak = 0
        for r in results:
            if r == 'loss':
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        f.write(f"Drawdown #{idx+1}:\n")
        f.write(f"   Trade range     : {start} → {end}  ({dd['trades_in_dd']} trades)\n")
        f.write(f"   Balance         : ${dd['start_balance']:,.2f} → ${dd['end_balance']:,.2f}\n")
        f.write(f"   Drawdown        : ${dd['dd_amount']:,.2f}  ({dd['dd_percent']:.1f}%)\n")
        f.write(f"   Win rate in DD  : {win_rate:.1f}%\n")
        f.write(f"   Longest loss streak: {max_streak} losses in a row\n")
        f.write("-" * 70 + "\n\n")
    
    # Overall summary
    if drawdowns:
        dd_amounts = [d['dd_amount'] for d in drawdowns]
        dd_percents = [d['dd_percent'] for d in drawdowns]
        f.write("=== OVERALL DRAWDOWN SUMMARY ===\n")
        f.write(f"Max drawdown amount : ${max(dd_amounts):,.2f}\n")
        f.write(f"Max drawdown %      : {max(dd_percents):.1f}%\n")
        f.write(f"Average drawdown %  : {np.mean(dd_percents):.1f}%\n")

print("✅ Drawdown analysis saved to: drawdown_analysis.txt")
print("You can now upload that file here for me to analyze.")
