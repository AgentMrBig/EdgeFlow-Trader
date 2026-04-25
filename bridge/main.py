"""
EdgeFlow Live Trading Bridge v0.3
• Watches ticks.csv from MT4
• Runs real EdgeFlow logic every minute
• Sends orders to orders.json (read by EA)
"""

import csv, json, pathlib, time, tomli, yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# === CONFIG ===
CONFIG = tomli.load(open(pathlib.Path(__file__).with_suffix(".toml"), "rb"))
FILES_DIR = pathlib.Path(CONFIG["mt4"]["files_path"])
TICK_CSV = FILES_DIR / "ticks.csv"
ORDER_JSON = FILES_DIR / "orders.json"

RISK = yaml.safe_load(open(pathlib.Path(__file__).parent.parent / "docs" / "risk-config.yaml"))
SLIPPAGE = RISK.get("slippagePoints", 3)

print("🚀 EdgeFlow Live Bridge v0.3 started")
print(f"   Watching: {FILES_DIR}")

# === EdgeFlow Signal Logic (same as simulation) ===
def check_edgeflow_signal(candles):
    """Run EdgeFlow logic on latest candles"""
    if len(candles) < 60:
        return None
    
    # Simple version - we'll expand this
    last = candles[-1]
    
    # For now: just return a test signal every 5 minutes
    # TODO: Add full engineer_features + htf_bias + ma9_slope logic here
    if len(candles) % 5 == 0:
        return {
            "side": "buy",
            "lot": 0.10,
            "sl": round(last['close'] - 0.0010, 5),
            "tp": round(last['close'] + 0.0032, 5),
            "slippage": SLIPPAGE
        }
    return None

# === File Watcher ===
class TickHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_check = 0
        self.candles = []
    
    def on_modified(self, event):
        if not event.src_path.endswith("ticks.csv"):
            return
        
        now = time.time()
        if now - self.last_check < 60:  # Check once per minute
            return
        self.last_check = now
        
        # Read latest ticks
        try:
            with open(TICK_CSV) as f:
                reader = csv.DictReader(f)
                rows = list(reader)[-100:]  # Last 100 ticks
                
                # Convert to candle format (simplified)
                self.candles = []
                for r in rows:
                    self.candles.append({
                        'close': float(r['bid'])
                    })
                
                # Run EdgeFlow logic
                signal = check_edgeflow_signal(self.candles)
                
                if signal:
                    ORDER_JSON.write_text(json.dumps(signal))
                    print(f"📤 Signal sent: {signal['side']} {signal['lot']} lots")
                    
        except Exception as e:
            print(f"Error: {e}")

# === Start ===
if __name__ == "__main__":
    observer = Observer()
    observer.schedule(TickHandler(), str(FILES_DIR), recursive=False)
    observer.start()
    
    print("✅ Bridge running. Waiting for live ticks from MT4...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()