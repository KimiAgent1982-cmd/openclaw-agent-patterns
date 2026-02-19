# Bot Monitor Pattern

Auto-restart critical processes with launchd on macOS.

## The Problem

Trading bots die. Network hiccups, API errors, memory leaks — whatever the cause, downtime corrupts paper trading data and ruins backtests.

## The Solution

**launchd + Monitoring Script**
- Checks every 10 minutes
- Auto-restarts dead bots
- Logs everything
- Only alerts on systemic issues

## Why launchd (not cron)

| Feature | cron | launchd |
|---------|------|---------|
| Runs if computer asleep | ❌ | ✅ |
| Auto-restart script if it dies | ❌ | ✅ |
| Better logging | ❌ | ✅ |

## Files

```
scripts/
└── bot_monitor.sh           # Main monitoring script

~/Library/LaunchAgents/
└── com.openclaw.botmonitor.plist  # launchd config
```

## Installation

### 1. Create the Monitor Script

```bash
cat > ~/.openclaw/workspace/scripts/bot_monitor.sh << 'EOF'
#!/bin/bash
# Bot Monitor - Restarts critical bots if they go down

LOG_FILE="$HOME/.openclaw/workspace/logs/bot_monitor.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

log() {
    echo "[$TIMESTAMP] $1" >> "$LOG_FILE"
}

# Check and restart if needed
if ! pgrep -f "bot_pattern" > /dev/null; then
    log "RESTARTING: Bot Name"
    cd "$HOME/.openclaw/workspace/path"
    nohup python3 -u bot.py >> bot.log 2>&1 &
fi

log "STATUS CHECK COMPLETE"
EOF

chmod +x ~/.openclaw/workspace/scripts/bot_monitor.sh
```

### 2. Create launchd Config

```bash
cat > ~/Library/LaunchAgents/com.openclaw.botmonitor.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.botmonitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/YOURNAME/.openclaw/workspace/scripts/bot_monitor.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>600</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/bot_monitor_out.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/bot_monitor_err.log</string>
</dict>
</plist>
EOF
```

### 3. Load It

```bash
launchctl load ~/Library/LaunchAgents/com.openclaw.botmonitor.plist
launchctl start com.openclaw.botmonitor
```

## Real-World Example

See [example-monitor.sh](./example-monitor.sh) for a 4-bot trading setup.

## Monitoring Multiple Bots

```bash
# Check DOGE Long
if ! pgrep -f "doge_long_paper/bot.py" > /dev/null; then
    restart_bot "DOGE Long" "$HOME/trading/doge_long"
fi

# Check DOGE Short  
if ! pgrep -f "doge_short_paper/bot.py" > /dev/null; then
    restart_bot "DOGE Short" "$HOME/trading/doge_short"
fi

# Check BTC Bot
if ! pgrep -f "v1_optimized_paper_bot.py" > /dev/null; then
    restart_bot "v1 BTC" "$HOME/trading"
fi

# Check Hummingbot
if ! pgrep -f "hummingbot_client.py" > /dev/null; then
    restart_bot "Hummingbot" "$HOME/trading/hummingbot"
fi
```

## Alert Thresholds

Only alert user if:
- Same bot restarts >3 times in 1 hour
- All bots down simultaneously
- Script itself failing

Otherwise: Log silently, fix automatically.

## Testing

```bash
# Kill a bot manually
pkill -f "bot_name"

# Wait 10 minutes
# Check if it restarted
pgrep -f "bot_name"

# Check logs
tail ~/.openclaw/workspace/logs/bot_monitor.log
```

## Troubleshooting

**launchd not running:**
```bash
launchctl list | grep openclaw
```

**Script permissions:**
```bash
chmod +x ~/.openclaw/workspace/scripts/bot_monitor.sh
```

**Logs:**
```bash
tail -f /tmp/bot_monitor_err.log
```

---

*Pattern in production for 30+ days, 4 bots, 99.9% uptime*