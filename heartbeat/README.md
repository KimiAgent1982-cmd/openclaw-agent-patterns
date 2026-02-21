# Heartbeat Integration Pattern

**Purpose:** Enable agents to perform periodic checks and proactive maintenance without manual intervention.

**Use Case:** Monitoring, health checks, periodic data collection, reminders, system maintenance.

---

## Core Concept

Agents wake up fresh each session with no memory of previous work. Heartbeats bridge this gap by scheduling periodic tasks that trigger agent actions even when no user is present.

**Key Insight:** The agent receives a heartbeat message, performs checks, and either reports findings or stays silent (HEARTBEAT_OK).

---

## Architecture

### Files
```
workspace/
├── HEARTBEAT.md          # Checklist of periodic tasks
├── memory/
│   └── heartbeat-state.json  # Track last check times
└── logs/
    ├── token_balance.json
    ├── bot_monitor.log
    └── system_health.json
```

### HEARTBEAT.md Structure

```markdown
# HEARTBEAT.md - Daily System Checks

## Checklist
- [ ] API token balance check
- [ ] Trading bot status
- [ ] Disk/RAM usage
- [ ] Security scan
- [ ] Sub-agent status

## Alerts Trigger
Report if:
- Token balance < threshold
- Any bot down > 15 minutes
- Disk usage > 85%
- Security anomalies detected
```

### State Tracking (heartbeat-state.json)

```json
{
  "lastChecks": {
    "token_balance": 1703275200,
    "bot_monitor": 1703275800,
    "security_scan": null
  },
  "alertThresholds": {
    "tokens_remaining": 10000000,
    "disk_percent": 85,
    "bot_downtime_minutes": 15
  }
}
```

---

## Implementation

### Python Heartbeat Script

```python
#!/usr/bin/env python3
"""
Heartbeat checker - runs via cron every 5 minutes
Logs results, triggers alerts only when needed.
"""
import json
import time
import subprocess
from pathlib import Path

WORKSPACE = Path("/Users/kimimini/.openclaw/workspace")
STATE_FILE = WORKSPACE / "memory/heartbeat-state.json"
LOG_DIR = WORKSPACE / "logs"

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"lastChecks": {}, "alertThresholds": {}}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def check_token_balance():
    """Check API token balance, alert if low."""
    result = subprocess.run(
        ["python3", "scripts/token_monitor.py", "--quiet"],
        capture_output=True, text=True
    )
    # Parse output, return status
    return "healthy"  # or "warning", "critical"

def check_bot_status():
    """Check if trading bots are running."""
    result = subprocess.run(
        ["ps", "aux"], capture_output=True, text=True
    )
    # Parse for bot processes
    return {"btc_v1": True, "doge_v1": True, "hummingbot": False}

def run_heartbeat():
    state = load_state()
    alerts = []
    
    # Token check (every 30 min)
    if time.time() - state["lastChecks"].get("token_balance", 0) > 1800:
        status = check_token_balance()
        if status != "healthy":
            alerts.append(f"Token balance: {status}")
        state["lastChecks"]["token_balance"] = time.time()
    
    # Bot check (every 10 min)
    if time.time() - state["lastChecks"].get("bot_monitor", 0) > 600:
        bots = check_bot_status()
        down_bots = [k for k, v in bots.items() if not v]
        if down_bots:
            alerts.append(f"Bots down: {', '.join(down_bots)}")
        state["lastChecks"]["bot_monitor"] = time.time()
    
    save_state(state)
    
    # Output for OpenClaw
    if alerts:
        print("⚠️ ALERTS:")
        for alert in alerts:
            print(f"  - {alert}")
        return 1  # Non-zero exit = alert
    else:
        print("HEARTBEAT_OK")
        return 0

if __name__ == "__main__":
    exit(run_heartbeat())
```

---

## Cron Configuration

```bash
# Edit crontab: crontab -e

# Run heartbeat every 5 minutes
*/5 * * * * cd ~/.openclaw/workspace && python3 scripts/heartbeat.py >> logs/heartbeat.log 2>&1

# Night mode (less frequent during sleep hours)
0 22-23,0-7 * * * cd ~/.openclaw/workspace && python3 scripts/heartbeat.py --night-mode >> logs/heartbeat.log 2>&1
```

---

## Agent Response Protocol

When receiving a heartbeat poll:

1. **Read HEARTBEAT.md** — Get the checklist
2. **Check thresholds** — Compare to state file
3. **Run quick checks** — Token balance, disk, etc.
4. **Report or stay silent:**
   - If all good → Reply `HEARTBEAT_OK`
   - If issues → Report specific problems

**Example Responses:**

```
HEARTBEAT_OK
```

```
⚠️ Trading bot down: Hummingbot
Token balance: 95M tokens (~19 days)
Disk usage: 2% (healthy)
```

---

## Best Practices

1. **Keep it lightweight** — Heartbeats run frequently, don't burn tokens
2. **Stateless checks** — Don't rely on session memory, read from files
3. **Alert fatigue** — Only report actionable issues
4. **Graceful degradation** — If a check fails, note it but don't crash
5. **Time-based batching** — Expensive checks less frequently

---

## Integration with OpenClaw

OpenClaw's cron system can trigger heartbeats:

```json
{
  "name": "agent_heartbeat",
  "schedule": {"kind": "every", "everyMs": 300000},
  "payload": {
    "kind": "systemEvent",
    "text": "Read HEARTBEAT.md if it exists. Follow it strictly. If nothing needs attention, reply HEARTBEAT_OK."
  }
}
```

---

## Related Patterns

- **Memory System** — Store heartbeat state
- **Bot Monitor** — Auto-restart from heartbeat alerts
- **Cost Optimization** — Use local LLM for heartbeats

*Next: Cost-Optimized Task Routing (3-tier LLM)*
