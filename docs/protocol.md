# docs/protocol.md  
*EdgeFlow Trader – Data & Command Protocol*  
**Version 0.1 (26-May-2025)**

---

## 1 Actors & Responsibilities

| Actor | Responsibility | File(s) Written | File(s) Read |
|-------|----------------|-----------------|--------------|
| **EA** (MQL4) | • Collect live ticks<br>• Execute orders<br>• Acknowledge fills | `ticks.csv` (✔︎)<br>`executions.csv` (Sprint-1) | `orders.json` |
| **Bridge** (FastAPI) | • Ingest ticks into TimescaleDB<br>• Publish orders via JSON<br>• Ingest execution acks (Sprint-1) | `orders.json` | `ticks.csv`<br>`executions.csv` |
| **TimescaleDB** | • Persist tick & execution history | _N/A_ | _N/A_ |
| **ML / Logic Core** | • Decide when to trade (future phase) | REST → `POST /order` | SQL (selects) |

All files reside in the MT4 “**Files**” directory:

```
C:\Users\<YOU>\AppData\Roaming\MetaQuotes\Terminal\<HASH>\MQL4\Files\
```

---

## 2 Tick Stream — `ticks.csv`

### Location  
Written by EA, tailed by Bridge.

### Schema (comma-separated)

| Column | Type | Example |
|--------|------|---------|
| `time` | `YYYY-MM-DD HH:MM:SS` (broker server TZ) | `2025-05-26 14:07:12` |
| `bid`  | `float` | `142.778` |
| `ask`  | `float` | `142.788` |
| `spread` | `float` (points) | `10.0` |

First row is the **header**.  
Bridge appends new rows and inserts them into table:

```sql
CREATE TABLE IF NOT EXISTS ticks(
  ts     TIMESTAMPTZ,
  bid    DOUBLE PRECISION,
  ask    DOUBLE PRECISION,
  spread DOUBLE PRECISION
);
```

---

## 3 Order Command — `orders.json`

### Location  
Written by Bridge, polled by EA every 250 ms.

### Payload (single JSON object)

```json
{
  "symbol": "USDJPY",
  "side"  : "buy",
  "lot"   : 0.25,
  "sl"    : 142.300,
  "tp"    : 143.050
}
```

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | `string` | MT4 symbol (case-sensitive). |
| `side` | `"buy"` \| `"sell"` | Trade direction. |
| `lot`  | `float` | Lot size (broker min step). |
| `sl`   | `float | null` | Stop-loss price (optional). |
| `tp`   | `float | null` | Take-profit price (optional). |

Bridge **overwrites** `orders.json` with one order object.  
EA reads JSON → `OrderSend()` → deletes the file.

---

## 4 Execution Ack — `executions.csv` *(planned Sprint-1)*

| Column | Type | Notes |
|--------|------|-------|
| `ticket` | `int` | MT4 order ticket. |
| `time` | `YYYY-MM-DD HH:MM:SS` | Open time. |
| `symbol` | `string` | Same as request. |
| `side` | `"buy"` \| `"sell"` | — |
| `lot` | `float` | Actual lot size. |
| `price` | `float` | Fill price. |

Bridge ingests rows and updates `executions` table:

```sql
CREATE TABLE IF NOT EXISTS executions(
  ticket  BIGINT PRIMARY KEY,
  ts      TIMESTAMPTZ,
  symbol  TEXT,
  side    TEXT,
  lot     DOUBLE PRECISION,
  price   DOUBLE PRECISION
);
```

---

## 5 Error Handling

| Layer | Scenario | Action |
|-------|----------|--------|
| EA | `OrderSend()` fails | Prints error code in Experts tab; leaves `orders.json` intact so Bridge can decide to retry or delete. |
| Bridge | Malformed CSV row | Skips row, logs `!! DB insert error …`. |
| Bridge | DB connection lost | Raises exception → process exit (code≠0) → external supervisor (PM2 / systemd) restarts. |
| Bridge | Invalid order JSON (missing field) | Returns HTTP 400 to client. |

---

## 6 Versioning & Compatibility

* **v0.1** – tick CSV & order JSON (this doc).  
* **v0.2** – add `executions.csv` and DB schema for fills.  
* **v0.3** – extend order JSON with `comment`, `magic`, and `type` (market vs pending).  

Changes are **append-only**; existing columns remain stable.

---

## 7 Example End-to-End Flow (v0.1)

1. EA writes  
   ```
   2025-05-26 14:07:12,142.778,142.788,10.0
   ```  
   to `ticks.csv`.
2. Bridge detects file change, inserts row into TimescaleDB.
3. ML core posts  
   ```
   POST /order {symbol:"USDJPY", side:"buy", lot:0.25}
   ```
4. Bridge writes same JSON to `orders.json`.
5. EA reads file, executes `OrderSend()`, prints confirmation, deletes file.

---

*© 2025 EdgeFlow Trader — All rights reserved.*
