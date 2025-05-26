"""
EdgeFlow Trader Bridge v0.1
• Watches MT4 Files folder for new tick rows → inserts into TimescaleDB
• Exposes POST /order → writes orders.json for EA to consume
"""
import os, time, csv, json, asyncio, pathlib, tomli
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

CONFIG = tomli.load(open(pathlib.Path(__file__).with_suffix('.toml'), 'rb'))
FILES_DIR = pathlib.Path(CONFIG['mt4']['files_path'])
TICK_CSV  = FILES_DIR / 'ticks.csv'
ORDER_JSON= FILES_DIR / 'orders.json'

# -- DB -----------------------------------------------------------------
conn = psycopg2.connect("dbname=edgeflow user=postgres password=postgres host=localhost port=5432")
cur  = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS ticks(
  ts TIMESTAMPTZ,
  bid DOUBLE PRECISION,
  ask DOUBLE PRECISION,
  spread DOUBLE PRECISION
);
""")
conn.commit()

def insert_tick(ts, bid, ask, spr):
    cur.execute("INSERT INTO ticks VALUES (%s,%s,%s,%s)", (ts,bid,ask,spr))
    conn.commit()

# -- file watcher -------------------------------------------------------
class TickHandler(FileSystemEventHandler):
    def __init__(self): self.seek = 0
    def on_modified(self, event):
        if event.src_path.endswith('ticks.csv'):
            with open(TICK_CSV, 'r') as f:
                f.seek(self.seek)
                reader = csv.reader(f)
                for row in reader:
                    if row and row[0]!='time':  # skip header
                        insert_tick(row[0], *map(float,row[1:]))
                self.seek = f.tell()

def start_watcher():
    handler = TickHandler()
    obs = Observer()
    obs.schedule(handler, str(FILES_DIR), recursive=False)
    obs.start()

# -- API ----------------------------------------------------------------
app = FastAPI(title="EdgeFlow Bridge")

class Order(BaseModel):
    symbol: str
    side:   str   # "buy" / "sell"
    lot:    float
    sl:     float | None = None
    tp:     float | None = None

@app.post("/order")
async def post_order(order: Order):
    try:
        ORDER_JSON.write_text(order.json())
        return {"status":"queued"}
    except Exception as e:
        raise HTTPException(500, str(e))

# -- bootstrap ----------------------------------------------------------
if __name__ == "__main__":      # python main.py
    start_watcher()
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
