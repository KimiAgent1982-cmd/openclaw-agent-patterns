# Agent Memory System

A production-ready memory architecture for OpenClaw agents.

## The Problem

Agents wake up fresh every session. Without persistence:
- "I forgot we decided that..."
- "What was I working on yesterday?"
- "Did I already tell the user about...?"

## The Solution

**Hybrid Memory Architecture:**
- Structured files for persistence
- Semantic search for recall
- Git for version control

## File Structure

```
workspace/
├── MEMORY.md                  # Curated long-term memory
├── memory/
│   ├── 2026-02-19.md         # Today's raw notes
│   ├── 2026-02-18.md         # Yesterday's notes
│   └── heartbeat-state.json  # State tracking
├── SOUL.md                   # Who you are
├── USER.md                   # Who they are
└── AGENTS.md                 # System rules
```

## MEMORY.md Template

```markdown
# MEMORY.md - Curated Long-Term Memory

## Active Projects
1. **Project Name** - Status, next steps

## Key Decisions
- YYYY-MM-DD: Decision made and why

## Important Context
- User preferences
- Ongoing issues
- Lessons learned

## Relationships
- How to address user
- Communication style
- Boundaries
```

## Daily File Template

```markdown
# 2026-02-19

## Morning
- What we did

## Decisions
- What was decided

## 3-Bullet Summary
1. Key thing 1
2. Key thing 2
3. Key thing 3
```

## Implementation

### Step 1: Create Files
```bash
mkdir -p memory
touch MEMORY.md memory/$(date +%Y-%m-%d).md
```

### Step 2: Read at Session Start
```python
# Read long-term memory
read("MEMORY.md")

# Read recent context
read(f"memory/{today}.md")
read(f"memory/{yesterday}.md")
```

### Step 3: Write Immediately
When something important happens:
```python
# Don't think "I'll remember this"
# WRITE IT NOW
edit("memory/2026-02-19.md", add="Critical decision made: ...")
```

### Step 4: Summarize
End of day, distill into 3 bullets:
```markdown
## 3-Bullet Summary
1. Launched trading bot v2
2. Fixed memory bug
3. User wants X by Friday
```

## Git Integration

```bash
# Auto-commit daily
git add memory/ MEMORY.md
git commit -m "Daily memory update $(date)"
git push
```

## Benefits

✅ **Survives restarts** — Files persist  
✅ **Fast recall** — Read only what you need  
✅ **Version control** — See how thinking evolved  
✅ **Transferable** — Share context with other agents  

## Real Example

See [example-memory.md](./example-memory.md) for a real (anonymized) session.

---

*Pattern tested in production for 30+ days*