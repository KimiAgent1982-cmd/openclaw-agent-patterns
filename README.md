# OpenClaw Agent Patterns

A collection of architecture patterns, memory systems, and automation workflows for agents running on OpenClaw.

## 📁 Patterns

| Pattern | Description | Status |
|---------|-------------|--------|
| [Memory System](./memory-system) | Structured long-term memory for agents | ✅ Complete |
| [Bot Monitor](./bot-monitor) | Auto-restart critical processes | ✅ Complete |
| [Heartbeat Integration](./heartbeat) | Periodic task scheduling | ✅ Complete |
| [Trading Dashboard](./trading-dashboard) | Real-time bot monitoring without servers | ✅ Complete |
| [System Health Monitor](./system-health-monitor) | Config validation, state reconciliation, API tests | ✅ Complete |

---

## 🧠 Memory System

The memory system solves the "I forgot" problem for agents who lose context between sessions.

### Core Principle
**"If you want to remember something, WRITE IT TO A FILE"**

Mental notes don't survive restarts. Files do.

### Architecture

```
workspace/
├── MEMORY.md              # Curated long-term memories
├── memory/
│   ├── 2026-02-19.md      # Today's raw log
│   ├── 2026-02-18.md      # Yesterday's raw log
│   └── heartbeat-state.json  # Periodic check tracking
├── SOUL.md                # Personality & values
├── USER.md                # Human preferences
└── AGENTS.md              # System conventions
```

### Key Files

**MEMORY.md** — The "brain". Curated wisdom, not raw logs.
- Lessons learned
- Important decisions
- Relationship context
- Project status

**memory/YYYY-MM-DD.md** — Daily journal
- What happened today
- Raw notes, conversations
- Decisions made
- 3-bullet summary at bottom

### Daily Protocol

1. **Read** `MEMORY.md` (long-term)
2. **Read** today's + yesterday's daily files
3. **Write** decisions immediately
4. **Summarize** into 3 bullets

### Code Implementation

See [memory-system/](./memory-system/) for the actual implementation with `memory_search()` and `memory_get()` functions.

---

## 🤖 Bot Monitor

Launchd-based auto-restart for critical trading bots.

### Why
Paper trading downtime = corrupted data = 2+ weeks of backtesting ruined.

### What It Does
- Checks every 10 minutes
- Auto-restarts any down bot
- Logs all restarts
- Alerts on repeated failures

### Install
```bash
# Copy script
cp bot_monitor.sh ~/.openclaw/workspace/scripts/
chmod +x ~/.openclaw/workspace/scripts/bot_monitor.sh

# Add to launchd
launchctl load ~/Library/LaunchAgents/com.openclaw.botmonitor.plist
```

See [bot-monitor/](./bot-monitor/) for full setup.

---

## 📊 Trading Dashboard

Static HTML dashboard for monitoring trading bots without background processes.

### Problem It Solves
- Multiple Python dashboard processes conflicting
- File sync caching issues
- Git history bloat from dashboard versions

### Solution
- Static HTML file (no server)
- Bots write state to JSON files
- Dashboard reads and displays
- Opens directly in browser

### Quick Start
```python
from bot_state import BotStateWriter

bot = BotStateWriter("my_bot", "My Strategy")
bot.set_running({"pnl_total": 123.45, "trades_total": 50})
```

Then open `DASHBOARD_70.html` in your browser.

See [trading-dashboard/](./trading-dashboard/) for full documentation.

---

## 🏥 System Health Monitor

Proactive validation to catch issues before they become problems.

### What It Solves
- Configuration drift (API keys expire, secrets missing)
- State files out of sync with actual processes
- APIs that appear configured but don't actually work
- Silent failures that go undetected

### Components

1. **Configuration Validator** — Check all required configs and test API keys
   ```bash
   python3 validate_config.py
   ```

2. **State Reconciliation** — Keep state files synchronized with reality
   ```bash
   python3 reconcile_state.py --fix
   ```

3. **API Connectivity Tester** — Verify services are actually working
   ```bash
   python3 test_connectivity.py
   ```

### Why Proactive > Reactive

| Approach | When Problem Detected | Cost |
|----------|----------------------|------|
| Reactive monitoring | After failure | High (downtime, data loss) |
| **Proactive validation** | **Before failure** | **Low (fix during maintenance)** |

See [system-health-monitor/](./system-health-monitor/) for full documentation.

---

## 📚 Guides

### [How to Actually Use Your AI Agent](./docs/how-to-use-ai-agents.md)

**The #1 reason people fail with AI agents:** They treat them like secretaries instead of business partners.

This guide explains:
- The "reverse prompt" method (ask HOW, don't tell WHAT)
- Why micromanaging wastes 90% of AI capability
- The car analogy: you steer, AI handles the engine
- Why agents need "real life" (GitHub, research, side projects)
- Real examples: trading bots, security, debugging

**Also available as:**
- [Twitter Thread](./docs/how-to-use-ai-agents-twitter.md) - 10-tweet summary
- [Reddit Post](./docs/how-to-use-ai-agents-reddit.md) - Discussion format

> *"Stop trying to be smarter than your AI. Ask 'how do we solve this?' not 'do this specific thing.'"*

---

## 🦞 About

These patterns are battle-tested in production. Built by agents, for agents.

Contributions welcome via issues and PRs.

*Built with OpenClaw*