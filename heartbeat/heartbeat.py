#!/usr/bin/env python3
"""
Heartbeat checker - Reference implementation
Logs results, triggers alerts only when needed.
"""
import json
import time
import subprocess
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw/workspace"
STATE_FILE = WORKSPACE / "memory/heartbeat-state.json"
LOG_DIR = WORKSPACE / "logs"

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {
        "lastChecks": {},
        "alertThresholds": {
            "tokens_remaining": 10_000_000,
            "disk_percent": 85,
            "bot_downtime_minutes": 15
        }
    }

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))

def check_token_balance():
    """Placeholder - integrate your token monitor."""
    return "healthy"

def check_disk_usage():
    """Check disk usage percentage."""
    result = subprocess.run(
        ["df", "-h", "/"], capture_output=True, text=True
    )
    # Parse output to get percentage
    return 50  # placeholder

def run_heartbeat():
    state = load_state()
    alerts = []
    
    # Your checks here
    # alerts.append("Example alert")
    
    save_state(state)
    
    if alerts:
        print("⚠️ ALERTS:")
        for alert in alerts:
            print(f"  - {alert}")
        return 1
    else:
        print("HEARTBEAT_OK")
        return 0

if __name__ == "__main__":
    exit(run_heartbeat())
