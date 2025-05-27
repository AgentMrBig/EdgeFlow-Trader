from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import csv
import os

app = FastAPI()

# Setup static and template folders
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")
templates = Jinja2Templates(directory="webapp/templates")

DATA_FILE = os.path.abspath("backtest/simulated_trades.csv")  # ✅ consistent shared path

def load_trade_stats():
    total_trades = 0
    winning_trades = 0
    total_profit = 0.0

    if not os.path.exists(DATA_FILE):
        return {
            "total_trades": 0,
            "win_rate": 0,
            "total_profit": 0.0,
            "open_trades": 0
        }

    with open(DATA_FILE, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pnl = float(row.get("pnl", 0))
            total_profit += pnl
            if pnl > 0:
                winning_trades += 1
            total_trades += 1

    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

    return {
        "total_trades": total_trades,
        "win_rate": round(win_rate, 2),
        "total_profit": round(total_profit, 2),
        "open_trades": 0  # simulation only, no live trades
    }

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    stats = load_trade_stats()
    equity_points = []
    equity = 0.0

    csv_path = os.path.abspath("backtest/simulated_trades.csv")

    if os.path.exists(csv_path):
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                pnl = float(row.get("pnl", 0))
                equity += pnl
                equity_points.append({
                    "x": row["timestamp"],
                    "y": round(equity, 2)
                })

    print(f"✅ Loaded {len(equity_points)} equity points")

    return templates.TemplateResponse("index.html", {
        "request": request,
        **stats,
        "points": equity_points
    })

