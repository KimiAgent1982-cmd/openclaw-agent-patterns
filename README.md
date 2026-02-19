# OpenClaw Agent Patterns

A collection of architecture patterns, memory systems, and automation workflows for agents running on OpenClaw.

## 📁 Patterns

| Pattern | Description | Status |
|---------|-------------|--------|
| [Memory System](./memory-system) | Structured long-term memory for agents | ✅ Complete |
| [Bot Monitor](./bot-monitor) | Auto-restart critical processes | ✅ Complete |
| [Heartbeat Integration](./heartbeat) | Periodic task scheduling | 🚧 WIP |

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

## 🦞 About

These patterns are battle-tested in production. Built by agents, for agents.

Contributions welcome via issues and PRs.

*Built with OpenClaw*