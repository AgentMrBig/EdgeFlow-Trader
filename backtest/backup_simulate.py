import shutil
import datetime
import os

def backup_current():
    """Create a timestamped backup of simulate_edgeflow.py"""
    src = "simulate_edgeflow.py"
    if not os.path.exists(src):
        print(f"❌ {src} not found!")
        return
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"simulate_edgeflow_backup_{timestamp}.py"
    
    shutil.copy2(src, backup_name)
    print(f"✅ Backup created: {backup_name}")

def restore_latest_backup():
    """Restore the most recent backup (optional manual use)"""
    backups = [f for f in os.listdir('.') if f.startswith("simulate_edgeflow_backup_") and f.endswith(".py")]
    if not backups:
        print("❌ No backups found!")
        return
    
    latest = max(backups)
    shutil.copy2(latest, "simulate_edgeflow.py")
    print(f"✅ Restored latest backup: {latest}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_latest_backup()
    else:
        backup_current()
