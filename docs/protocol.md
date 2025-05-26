# docs/protocol.md  
*EdgeFlow Trader – Data & Command Protocol*  
**Version 0.2 (26-May-2025)**

---

## 1 Actors & Responsibilities

| Actor | Responsibility | File(s) Written | File(s) Read |
|-------|----------------|-----------------|--------------|
| **EA** (MQL4) | • Collect live ticks<br>• Execute orders<br>• Acknowledge fills | `ticks.csv`, `executions.csv` | `orders.json` |
| **Bridge** (FastAPI) | • Ingest ticks into DB<br>• Validate & write order JSON<br>• Ingest fills from EA | `orders.json` | `ticks.csv`, `executions.csv` |
| **TimescaleDB** | • Persist tick & execution history | — | — |
| **ML Logic (future)** | • Analyze ticks<br>• Generate orders via REST | — | `/order` endpoint, Timescale data |

---

## 2 Tick Stream — `ticks.csv`

### Location  
Written by EA, tailed by Bridge.

### Format (CSV)

```
time,bid,ask,spread
2025-05-26 14:07:12,142.778,142.788,10.0
```

| Column | Type | Example |
|--------|------|---------|
| `time` | `string` – `YYYY-MM-DD HH:MM:SS` | `2025-05-26 14:07:12` |
| `bid`  | `float` | `142.778` |
| `ask`  | `float` | `142.788` |
| `spread` | `float` (points) | `10.0` |

Inserted into TimescaleDB table:

```sql
CREATE TABLE ticks (
  ts     TIMESTAMPTZ,
  bid    DOUBLE PRECISION,
  ask    DOUBLE PRECISION,
  spread DOUBLE PRECISION
);
```

---

## 3 Order Command — `orders.json`

### Location  
Written by Bridge, read by EA every tick.

### Format (JSON)

```json
{
  "symbol": "USDJPY",
  "side":   "buy",
  "lot":    0.25,
  "sl":     null,
  "tp":     null,
  "slippage": 3
}
```

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | `string` | MT4 symbol (case-sensitive) |
| `side` | `"buy"` or `"sell"` | Direction |
| `lot` | `float` | Size in lots |
| `sl`, `tp` | `float` or `null` | Optional SL/TP price |
| `slippage` | `int` | Max price drift (in points) allowed |

→ The EA deletes the file after processing.

---

## 4 Execution Ack — `executions.csv` (v0.2+)

### Location  
Written by EA, tailed by bridge

### Format (CSV)

```
ticket,time,symbol,side,lot,price
12345678,2025-05-26 14:08:02,USDJPY,buy,0.25,142.784
```

| Column | Type | Description |
|--------|------|-------------|
| `ticket` | `int` | MT4 trade ticket ID |
| `time` | `string` – `YYYY-MM-DD HH:MM:SS` | Order fill time |
| `symbol` | `string` | — |
| `side` | `"buy"` or `"sell"` | Direction |
| `lot` | `float` | Executed lot size |
| `price` | `float` | Fill price |

Inserted into TimescaleDB:

```sql
CREATE TABLE executions (
  ticket  BIGINT PRIMARY KEY,
  ts      TIMESTAMPTZ,
  symbol  TEXT,
  side    TEXT,
  lot     DOUBLE PRECISION,
  price   DOUBLE PRECISION
);
```

---

## 5 Error Handling & Recovery

| Component | Failure | Recovery Behavior |
|-----------|---------|-------------------|
| EA | Invalid JSON | Prints warning, skips file |
| EA | OrderSend fails | Logs error, does not write to executions.csv |
| Bridge | Malformed CSV row | Skips row, logs `!! DB insert error` |
| Bridge | Invalid JSON on POST | HTTP 400 |
| Bridge | `orders.json` write fails | HTTP 500 |
| Bridge | `executions.csv` missing | Waits for file to appear, no crash |

---

## 6 Version History

| Version | Summary |
|---------|---------|
| **0.1** | Tick ingestion, order queueing |
| **0.2** | Added order execution, `executions.csv`, `slippage` config |
| _(next)_ | Planned: fill-to-position logic, profit calc, ML trade loop |

---

*© 2025 EdgeFlow Trader — All rights reserved.*
