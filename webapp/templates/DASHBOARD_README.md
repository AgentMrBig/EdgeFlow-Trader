# EdgeFlow Dashboard - Phase 1

## What Was Built

Phase 1 Complete: Clean dashboard layout + Candlestick chart as reusable component.

### Files Created

webapp/templates/
├── dashboard.html                     # Main layout (header + sidebar + chart)
└── components/
    └── candles_chart.html             # Reusable candlestick component

## How to Use

### 1. Copy into your project

You already have both files.

### 2. Add this route in your FastAPI main.py

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

### 3. Make sure these static files exist

- /static/usdjpy_m1.csv
- /static/trades.json

### 4. Visit /dashboard

## Current Features

- Modern dark trading UI (Tailwind)
- Left sidebar with simulation controls (Risk, SL, TP, Spread sliders)
- Main candlestick chart with:
  - 9/20/100/200 SMA + Bollinger Bands
  - Trade markers (triangles + dashed lines)
  - Hover tooltips with Balance Before/After
  - Proper xxx.xxx JPY formatting
- Bottom metrics row (Win Rate, PnL, Max DD, Profit Factor)

## Next Steps (Phase 2)

- Add Equity Curve component
- Connect "Run 1-Day Backtest" button to real backend
- Live refresh of charts + stats after simulation

Status: Phase 1 complete. Ready for equity curve + real backend integration.