from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

app = FastAPI(title="EdgeFlow Trader")

# === NO CACHE MIDDLEWARE (prevents stale data) ===
class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static/") or request.url.path == "/dashboard":
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheMiddleware)

app.mount("/static", StaticFiles(directory="webapp/static"), name="static")
templates = Jinja2Templates(directory="webapp/templates")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")

# ... rest of your code stays exactly the same ...

@app.post("/api/run_simulation")
async def run_simulation(request: Request):
    try:
        data = await request.json()
        
        # Basic parameters
        risk = float(data.get("risk", 2.0)) / 100
        sl_mult = float(data.get("sl", 1.1))
        tp_mult = float(data.get("tp", 3.2))
        spread = float(data.get("spread", 9))
        
        # Advanced parameters
        cooldown = int(data.get("cooldown", 15))
        max_hold = int(data.get("max_hold", 12))
        session = data.get("session", "All")
        
        # NEW: Data Range
        data_range = data.get("data_range", "1")
        start_date = data.get("start_date", "")
        end_date = data.get("end_date", "")
        
        print(f"🚀 Running REAL simulation: range={data_range}, risk={risk*100}%, SL={sl_mult}x, TP={tp_mult}x")
        
        from feature_engineer import engineer_features
        
        # Load full data
        df_raw = pd.read_csv("webapp/static/usdjpy_m1.csv")
        df_raw['timestamp'] = pd.to_datetime(df_raw['Date'].astype(str) + ' ' + df_raw['Timestamp'])
        df_raw = df_raw.sort_values('timestamp')
        
        # === CALCULATE DATA SLICE ===
        total_candles = len(df_raw)
        
        if data_range == "custom" and start_date and end_date:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date) + timedelta(days=1)
            mask = (df_raw['timestamp'] >= start) & (df_raw['timestamp'] < end)
            one_day = df_raw[mask].reset_index(drop=True)
        elif data_range == "1":
            one_day = df_raw.iloc[-1440:].reset_index(drop=True)
        elif data_range == "3":
            one_day = df_raw.iloc[-4320:].reset_index(drop=True)
        elif data_range == "7":
            one_day = df_raw.iloc[-10080:].reset_index(drop=True)
        elif data_range == "30":
            one_day = df_raw.iloc[-43200:].reset_index(drop=True)
        elif data_range == "full":
            one_day = df_raw.reset_index(drop=True)
        else:
            one_day = df_raw.iloc[-1440:].reset_index(drop=True)
        
        if len(one_day) == 0:
            return JSONResponse({
                "status": "error",
                "message": "No data found for selected range"
            }, status_code=400)
        
        df = engineer_features(one_day, lookback=60)
        
        START_BALANCE = 100.0
        MAX_HOLD_CANDLES = max_hold
        COOLDOWN_CANDLES = cooldown
        SPREAD_POINTS = spread
        SL_ATR_MULT = sl_mult
        TP_ATR_MULT = tp_mult
        RISK_PER_TRADE = risk
        MAX_LOT_SIZE = 100.0
        MARGIN_PER_LOT = 50.0
        TRADE_SESSIONS = session
        
        balance = START_BALANCE
        trades = []
        consecutive_losses = 0
        cooldown_until = -1
        
        for i in range(60, len(df) - MAX_HOLD_CANDLES):
            current = df.iloc[i]
            sess = current['session']
            
            if TRADE_SESSIONS != "All" and sess != TRADE_SESSIONS:
                continue
            
            if i < cooldown_until:
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
                continue
            
            direction = 'buy' if long_signal else 'sell'
            mid_price = current['Close']
            spread_val = SPREAD_POINTS * 0.0001
            entry_price = mid_price + (spread_val / 2) if direction == 'buy' else mid_price - (spread_val / 2)
            
            atr = current['atr_14']
            sl_dist = SL_ATR_MULT * atr
            tp_dist = TP_ATR_MULT * atr
            
            risk_amount = balance * RISK_PER_TRADE
            lot_size = max(0.01, min(round(risk_amount / (sl_dist * 100), 2), MAX_LOT_SIZE))
            
            if lot_size * MARGIN_PER_LOT > balance * 0.6:
                continue
            
            exit_price = None
            result = None
            
            for j in range(1, MAX_HOLD_CANDLES + 1):
                fut = df.iloc[i + j]
                if direction == 'buy':
                    if fut['High'] - entry_price >= tp_dist:
                        exit_price = entry_price + tp_dist - (spread_val / 2)
                        result = 'win'
                        break
                    if entry_price - fut['Low'] >= sl_dist:
                        exit_price = entry_price - sl_dist + (spread_val / 2)
                        result = 'loss'
                        break
                else:
                    if entry_price - fut['Low'] >= tp_dist:
                        exit_price = entry_price - tp_dist + (spread_val / 2)
                        result = 'win'
                        break
                    if fut['High'] - entry_price >= sl_dist:
                        exit_price = entry_price + sl_dist - (spread_val / 2)
                        result = 'loss'
                        break
            
            if exit_price is None:
                final = df.iloc[i + MAX_HOLD_CANDLES]
                exit_price = final['Close']
                result = 'win' if (direction == 'buy' and exit_price > entry_price) or (direction == 'sell' and exit_price < entry_price) else 'loss'
            
            pip_diff = (exit_price - entry_price) if direction == 'buy' else (entry_price - exit_price)
            profit = pip_diff * lot_size * 1000
            
            balance += profit
            
            trades.append({
                "timestamp": int(current.name.timestamp()),  # ← Unix timestamp (number)
                "direction": direction,
                "entry": round(entry_price, 3),
                "exit": round(exit_price, 3),
                "profit": round(profit, 2),
                "result": result,
                "lot_size": lot_size
            })
            
            if result == 'loss':
                consecutive_losses += 1
                if consecutive_losses >= 2:
                    cooldown_until = i + COOLDOWN_CANDLES
                    consecutive_losses = 0
            else:
                consecutive_losses = 0
        
        with open("webapp/static/trades.json", "w") as f:
            json.dump(trades, f)
        
        equity = 100
        equity_data = []
        for t in trades:
            equity += t["profit"]
            equity_data.append({"timestamp": t["timestamp"], "balance": round(equity, 2)})
        
        with open("webapp/static/equity_data.json", "w") as f:
            json.dump(equity_data, f)
        
        # === DETAILED CONSOLE OUTPUT ===
        win_rate = round(sum(1 for t in trades if t["result"] == "win") / len(trades) * 100, 2) if trades else 0
        total_wins = sum(1 for t in trades if t["result"] == "win")
        total_losses = len(trades) - total_wins
        final_balance = balance
        
        print(f"""
✅ REAL simulation complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Total Trades: {len(trades)}
✅ Wins: {total_wins}
❌ Losses: {total_losses}
📈 Win Rate: {win_rate}%
💰 Final Balance: ${final_balance:,.2f}
📈 Net PnL: ${final_balance - 100:,.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
        
        return JSONResponse({
            "status": "success",
            "message": f"Simulation complete! {len(trades)} trades | Win Rate: {win_rate}% | Balance: ${balance:.2f}",
            "trades_count": len(trades),
            "win_rate": win_rate,
            "net_pnl": round(balance - 100, 2)
        })
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return JSONResponse({
            "status": "error",
            "message": f"Simulation failed: {str(e)}"
        }, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)