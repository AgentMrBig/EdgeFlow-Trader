"""
EdgeFlow Trader Bridge  v0.2
• Ingests ticks.csv into TimescaleDB
• POST /order with risk guard → orders.json  (adds slippage from YAML)
• Watches executions.csv → inserts fills into DB
"""

import csv, json, pathlib, tomli, psycopg2, yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# ------------------------------------------------------------------- config
CONFIG = tomli.load(open(pathlib.Path(__file__).with_suffix(".toml"), "rb"))
FILES_DIR = pathlib.Path(CONFIG["mt4"]["files_path"])
TICK_CSV  = FILES_DIR / "ticks.csv"
ORDER_JSON= FILES_DIR / "orders.json"
EXEC_CSV  = FILES_DIR / "executions.csv"

RISK = yaml.safe_load(open(pathlib.Path(__file__).parent.parent / "docs" / "risk-config.yaml"))

SLIPPAGE = RISK.get("slippagePoints", 3)

print(">> Bridge watching:", FILES_DIR)

# ------------------------------------------------------------------- DB
conn = psycopg2.connect(
    "dbname=edgeflow user=postgres password=postgres host=localhost port=5432"
)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS ticks(
  ts TIMESTAMPTZ,
  bid DOUBLE PRECISION,
  ask DOUBLE PRECISION,
  spread DOUBLE PRECISION
);""")
cur.execute("""
CREATE TABLE IF NOT EXISTS executions(
  ticket  BIGINT PRIMARY KEY,
  ts      TIMESTAMPTZ,
  symbol  TEXT,
  side    TEXT,
  lot     DOUBLE PRECISION,
  price   DOUBLE PRECISION
);""")
conn.commit()

def insert_tick(row):
    cur.execute("INSERT INTO ticks VALUES (%s,%s,%s,%s)", row)
    conn.commit()
    print("DB tick:", row[0])

def insert_exec(row):
    cur.execute("""INSERT INTO executions VALUES (%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (ticket) DO NOTHING""", row)
    conn.commit()
    print("DB exec:", row[0])

# ------------------------------------------------------------------- file watchers
class TickHandler(FileSystemEventHandler):
    def __init__(self): self.seek = 0
    def on_modified(self, event):
        if not event.src_path.endswith("ticks.csv"): return
        with open(TICK_CSV) as f:
            f.seek(self.seek)
            rdr = csv.reader(f)
            for r in rdr:
                if len(r)!=4 or r[0]=="time": continue
                insert_tick(r)
            self.seek = f.tell()

class ExecHandler(FileSystemEventHandler):
    def __init__(self): self.seek = 0
    def on_modified(self, event):
        if not event.src_path.endswith("executions.csv"): return
        with open(EXEC_CSV) as f:
            f.seek(self.seek)
            rdr = csv.reader(f)
            for r in rdr:
                if len(r)!=6 or r[0]=="ticket": continue
                insert_exec(r)
            self.seek = f.tell()

def start_watchers():
    obs = Observer()
    obs.schedule(TickHandler(), str(FILES_DIR), recursive=False)
    obs.schedule(ExecHandler(), str(FILES_DIR), recursive=False)
    obs.start()


# ------------------------------------------------------------------- FastAPI
app = FastAPI(title="EdgeFlow Bridge v0.2")

class Order(BaseModel):
    symbol: str
    side  : str
    lot   : float
    sl    : float | None = None
    tp    : float | None = None

def risk_check(o: dict):
    # lot increment check (0.01 multiple)
    if round(o["lot"] * 100) % 1 != 0:
        raise ValueError("lot must be multiple of 0.01")

    # open trade cap (counting executions as positions)
    cur.execute("SELECT COUNT(*) FROM executions")
    if cur.fetchone()[0] >= RISK["maxOpenTrades"]:
        raise ValueError("maxOpenTrades exceeded")

@app.post("/order")
async def post_order(order: Order):
    try:
        o = order.dict()
        o["slippage"] = SLIPPAGE
        risk_check(o)
        ORDER_JSON.write_text(json.dumps(o))
        return {"status":"queued"}
    except Exception as exc:
        raise HTTPException(400, str(exc))

# ------------------------------------------------------------------- bootstrap
@app.on_event("startup")
def _startup():
    start_watchers()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)

    print(app.routes)

