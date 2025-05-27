import os
import csv
import json

csv_path = "simulated_trades.csv"


output_path = os.path.join(os.path.dirname(__file__), "../webapp/static/equity_data.json")
output_path = os.path.abspath(output_path)


points = []
equity = 0.0

with open(csv_path, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        pnl = float(row.get("pnl", 0))
        equity += pnl
        points.append({
            "x": row["timestamp"],
            "y": round(equity, 2)
        })

with open(output_path, "w") as out:
    json.dump(points, out, indent=2)

print(f"✅ Exported {len(points)} equity points to {output_path}")
