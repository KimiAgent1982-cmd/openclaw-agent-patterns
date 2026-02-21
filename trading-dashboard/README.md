# Trading Dashboard Pattern

**Purpose:** Real-time monitoring dashboard for trading bots without background processes or server conflicts.

**Use Case:** Monitor multiple trading bots from a single web interface without running Python servers.

---

## Problem

Traditional dashboard approaches cause conflicts:
- Multiple Python processes competing for ports
- File sync caching issues
- Git history bloat from multiple dashboard versions
- Launchd jobs auto-restarting old versions

## Solution

**Static HTML dashboard** that reads from JSON state files:
- No Python server needed
- No background processes
- Opens directly in browser
- Bots write state, dashboard reads it

---

## Architecture

```
workspace/
├── state/                    # Bot state files (JSON)
│   ├── btc_long_v1.json
│   ├── mm_1h.json
│   └── grid_btc.json
├── trading/
│   └── bot_state.py         # State writer library
├── DASHBOARD_70.html        # Static dashboard (opens in browser)
└── DASHBOARD_OPS.html       # Operations dashboard
```

### Data Flow

```
┌─────────────┐     JSON      ┌─────────────────┐
│ Trading Bot │ ────────────► │ state/bot.json  │
│   (Python)  │   write       │  (state file)   │
└─────────────┘               └─────────────────┘
                                        │
                                        │ fetch()
                                        ▼
                              ┌─────────────────┐
                              │  Dashboard.html │
                              │ (Browser/JS)    │
                              └─────────────────┘
```

---

## Bot State Writer

### Installation

Copy `bot_state.py` to your trading directory:

```bash
cp trading-dashboard/bot_state.py ~/workspace/trading/
```

### Usage

```python
from bot_state import BotStateWriter

# Initialize state writer
bot = BotStateWriter("mm_1h", "Market Maker 1H")

# Set running status
bot.set_running({
    "pnl_total": 123.45,
    "pnl_24h": 12.34,
    "trades_total": 50
})

# Update position
bot.update_position("long", 0.5, entry_price=45000.00)

# Record a trade
bot.record_trade(pnl=2.5, side="sell")

# Handle errors
bot.set_error("API connection failed")
```

### State Schema

```json
{
  "bot_id": "mm_1h",
  "bot_name": "Market Maker 1H",
  "status": "running",
  "status_color": "green",
  "pnl_total": 123.45,
  "pnl_24h": 12.34,
  "trades_total": 50,
  "trades_24h": 5,
  "position": {
    "side": "long",
    "size": 0.5,
    "entry_price": 45000.00,
    "opened_at": "2026-02-21T10:00:00Z"
  },
  "last_trade": {
    "time": "2026-02-21T10:30:00Z",
    "pnl": 2.5,
    "side": "sell"
  },
  "last_update": "2026-02-21T10:30:00Z",
  "last_error": null,
  "uptime_seconds": 3600,
  "version": "1.0.0"
}
```

---

## Dashboard Features

### Trading Dashboard (DASHBOARD_70.html)

- **Bot Cards**: Visual status of each bot
- **PnL Tracking**: Total and 24h profit/loss
- **Position Display**: Current open positions
- **Trade History**: Recent trades
- **Auto-refresh**: Updates every 10 seconds
- **Status Colors**: Green (running), Yellow (paused), Red (error)

### Operations Dashboard (DASHBOARD_OPS.html)

- **System Checklist**: Daily/weekly tasks
- **Metrics**: Disk usage, token balance
- **Quick Links**: Common operations
- **Alert Log**: Recent system events

---

## Opening the Dashboard

### Option 1: Direct File Open (Simplest)

```bash
open DASHBOARD_70.html
```

### Option 2: Local HTTP Server

```bash
cd ~/.openclaw/workspace
python3 -m http.server 8080
# Open http://localhost:8080/DASHBOARD_70.html
```

### Option 3: Cron Auto-Open

```bash
# Add to crontab for daily morning check
0 9 * * * open ~/.openclaw/workspace/DASHBOARD_70.html
```

---

## Integration Example

### In Your Trading Bot

```python
#!/usr/bin/env python3
import asyncio
from bot_state import BotStateWriter

class MyTradingBot:
    def __init__(self):
        self.state = BotStateWriter("my_bot", "My Strategy")
        self.state.set_running()
    
    async def on_fill(self, trade):
        """Called when order fills."""
        self.state.record_trade(
            pnl=trade.realized_pnl,
            side=trade.side
        )
    
    async def on_error(self, error):
        """Called on error."""
        self.state.set_error(str(error))
    
    async def update_position(self, position):
        """Update position state."""
        if position:
            self.state.update_position(
                side=position.side,
                size=position.size,
                entry_price=position.entry_price
            )
        else:
            self.state.update_position(None, 0)
```

---

## Best Practices

1. **Write State After Every Action**
   - Don't batch updates
   - Dashboard should always show current state

2. **Handle Errors Gracefully**
   - Set status to "error" on exceptions
   - Include error message in `last_error`

3. **Atomic Writes**
   - State writer uses temp-file + rename
   - Dashboard never reads partial JSON

4. **Keep State Small**
   - Don't store full trade history
   - Store summary stats + last N trades

5. **Version Your State**
   - Include version field for migrations

---

## Troubleshooting

### Dashboard Shows "No Bots"

```bash
# Check state files exist
ls ~/.openclaw/workspace/state/

# Check state is valid JSON
cat ~/.openclaw/workspace/state/mm_1h.json | python3 -m json.tool
```

### State Not Updating

```bash
# Check file permissions
ls -la ~/.openclaw/workspace/state/

# Restart bot with state writer
```

### Dashboard Not Loading

```bash
# Try direct file open
open ~/.openclaw/workspace/DASHBOARD_70.html

# Check browser console for JS errors
```

---

## Related Patterns

- **Bot Monitor** — Auto-restart bots that show "error" status
- **Heartbeat** — Check dashboard status periodically
- **Memory System** — Store trading history and decisions

---

*Next: Cost-Optimized API Routing*
