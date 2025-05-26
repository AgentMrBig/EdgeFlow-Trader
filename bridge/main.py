"""
EdgeFlow Trader bridge  v0.1d
• Watches MT4 ticks.csv → inserts rows into TimescaleDB
• POST /order  →  writes orders.json for the EA
"""

import csv, json, pathlib
import psycopg2, tomli
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# ----------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------
CONFIG = tomli.load(open(pathlib.Path(__file__).with_suffix(".toml"), "rb"))
FILES_DIR = pathlib.Path(CONFIG["mt4"]["files_path"])
TICK_CSV  = FILES_DIR / "ticks.csv"
ORDER_JSON = FILES_DIR / "orders.json"
print(">> Bridge watching:", FILES_DIR)

# ----------------------------------------------------------------------
# Database
# ----------------------------------------------------------------------
conn = psycopg2.connect(
    "dbname=edgeflow user=postgres password=postgres host=localhost port=5432"
)
cur = conn.cursor()
cur.execute(
    """CREATE TABLE IF NOT EXISTS ticks(
           ts TIMESTAMPTZ,
           bid DOUBLE PRECISION,
           ask DOUBLE PRECISION,
           spread DOUBLE PRECISION
       );"""
)
conn.commit()

def insert_tick(ts, bid, ask, spr):
    cur.execute("INSERT INTO ticks VALUES (%s,%s,%s,%s)", (ts,bid,ask,spr))
    conn.commit()
    print("DB insert:", ts, bid, ask)        # debug line

# ----------------------------------------------------------------------
# File-watcher
# ----------------------------------------------------------------------
class TickHandler(FileSystemEventHandler):
    def __init__(self): self.seek = 0
    def on_modified(self, event):
        if not event.src_path.endswith("ticks.csv"): return
        with open(TICK_CSV, "r") as f:
            f.seek(self.seek)
            reader = csv.reader(f)
            for row in reader:
                if len(row) != 4 or row[0] == "time":   # skip bad rows
                    continue
                try:
                    insert_tick(row[0], *map(float, row[1:]))
                except Exception as e:
                    print("!! DB insert error:", e, "row=", row)
            self.seek = f.tell()

def start_watcher():
    handler = TickHandler()
    obs = Observer()
    obs.schedule(handler, str(FILES_DIR), recursive=False)
    obs.start()

# ----------------------------------------------------------------------
# FastAPI app
# ----------------------------------------------------------------------
app = FastAPI(title="EdgeFlow Bridge")

@app.on_event("startup")
def _startup():
    """Start the CSV file-watcher in the *worker* process."""
    start_watcher()

class Order(BaseModel):
    symbol: str
    side: str
    lot: float
    sl: float | None = None
    tp: float | None = None

@app.post("/order")
async def post_order(order: Order):
    try:
        ORDER_JSON.write_text(order.json())
        return {"status": "queued"}
    except Exception as exc:
        raise HTTPException(500, str(exc))

# ----------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)   # ← no --reload
