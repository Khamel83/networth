# How to Improve ONE_SHOT: Patterns from Your Development Work

**Analysis Date**: 2025-11-26  
**Projects Analyzed**: Atlas, Atlas-voice, Divorce, Frugalos/Hermes, Homelab, Tablo, TrojanHorse, VDD/OOS  
**Purpose**: Extract the recurring ethos, patterns, and lessons to refine ONE_SHOT

---

## Executive Summary

After deep analysis of your 8 major projects, here's the **connecting thread**: You build **pragmatic, self-documenting systems that solve real problems with minimal dependencies and maximum automation**. You're not building tech demos—you're building tools you actually use, and you obsess over making them maintainable by future-you.

**The Core Philosophy** (distilled from all projects):
1. **Documentation IS the product** - READMEs that explain WHY, not just HOW
2. **Automation over manual work** - If you do it twice, script it
3. **Local-first, then network** - Own your data, cloud is optional
4. **Cost-conscious AI** - Cheap models first, upgrade only when necessary
5. **Simplicity through constraints** - SQLite over Postgres, shell over Python when possible
6. **Real-world validation** - Every project solves a problem you actually have

---

## 🎯 THEME 1: Documentation as First-Class Citizen

### What You Do (Consistently)

**Every project has**:
- Multiple README files at different levels (main, subsystems, workflows)
- Explicit "Quick Start" sections (5-minute setup targets)
- "What This Is" and "What This Does" upfront
- Status indicators (✅ COMPLETE, 🔄 IN PROGRESS, ⏳ PENDING)
- Clear file structure documentation
- Troubleshooting sections

**Examples**:
- **Divorce**: `QUICK_START_LEGAL_TEAM.md`, `QUICK_START_EXTRACTION.md` - role-specific docs
- **Homelab**: `START_HERE.md` → navigation hub, `DEPLOY.md` → step-by-step execution
- **OOS**: Comprehensive doc hierarchy with `QUICK_START.md`, `DEPLOYMENT.md`, `CLAUDE_CODE_INTEGRATION.md`
- **Atlas**: API documentation, status scripts, multiple integration guides

### The Pattern

```markdown
# Project Name - One-Line Description

**Status**: [Current state with emoji]
**Quick Start**: [Literally 3-5 commands to get running]

## 🎯 What It Does
[Problem → Solution in 2-3 sentences]

## 🚀 Quick Start
[Copy-paste commands, no thinking required]

## 📁 File Structure
[What's where and why]

## 🆘 Troubleshooting
[Common issues you've actually hit]
```

### ONE_SHOT Improvement

**Add to Section 6 (PRD Generation)**:
```markdown
## 6.9 Documentation Requirements

Every ONE_SHOT project MUST include:

1. **README.md** with:
   - One-sentence "What This Is"
   - Status badge/indicator
   - Quick Start (≤5 commands)
   - File structure explanation
   - Troubleshooting section (populated as issues arise)

2. **QUICK_START.md** (if project is complex):
   - 5-minute setup target
   - Copy-paste commands only
   - No explanations (link to main README for details)

3. **WHY.md** (for non-trivial architectural choices):
   - Document decisions that aren't obvious
   - "We chose X over Y because..."
   - Link to relevant ADRs if using Architecture Decision Records

4. **Status Indicators**:
   - Use emoji consistently: ✅ ⏳ 🔄 ❌ ⚠️
   - Update as project evolves
   - Make status visible in README header
```

---

## 🏗️ THEME 2: Pragmatic Architecture Patterns

### What You Actually Build

**Recurring Stack**:
- **Language**: Python (90% of projects) - you know it, it works
- **Storage**: SQLite → PostgreSQL progression (start simple, upgrade when needed)
- **Config**: `.env` files + YAML for complex configs
- **CLI**: `click` or `typer` for argument parsing
- **Web**: FastAPI when needed (not Flask, not Django)
- **Deployment**: systemd + Tailscale (homelab pattern)
- **Containerization**: Docker Compose with modular includes
- **AI**: OpenRouter → Gemini Flash Lite default, upgrade reluctantly

**Storage Philosophy** (from all projects):
```
Small data (< 1K items) → Files (YAML/JSON)
Medium data (1K-100K) → SQLite
Large data (100K+) → PostgreSQL
Mixed → Files for raw, SQLite for processed (Divorce, TrojanHorse pattern)
```

### The "Start Simple, Upgrade When Forced" Pattern

**Atlas**: Started with simple file-based config, evolved to database tracking  
**Divorce**: SQLite for 135K records (works great, no need for Postgres)  
**TrojanHorse**: Files for raw notes, SQLite for processed/indexed  
**Homelab**: Docker Compose, not Kubernetes (complexity not justified)

### Anti-Pattern You Avoid

❌ **Over-engineering upfront**:
- You don't use Kubernetes (Docker Compose is enough)
- You don't use complex ORMs (raw SQL or simple query builders)
- You don't use microservices (monolith until proven otherwise)
- You don't use NoSQL (relational is fine)

### ONE_SHOT Improvement

**Add to Section 1.3 (Simplicity First)**:
```markdown
## 1.3.1 The Upgrade Path Principle

**Start with the simplest thing that works, upgrade only when you hit limits.**

Storage progression:
1. Files (YAML/JSON) → works for < 1K items
2. SQLite → works for < 100K items, single-file portability
3. PostgreSQL → only when you need multi-user, complex queries, or > 100K items

Deployment progression:
1. Local script → works for personal use
2. systemd service → works for 24/7 single-machine
3. Docker Compose → works for multi-service, easy rollback
4. Kubernetes → only if you need multi-machine orchestration (you probably don't)

**Document your current tier and upgrade triggers**:
```yaml
# In README.md
Current Tier: SQLite (15K records)
Upgrade Trigger: > 100K records OR multi-user access needed
Next Tier: PostgreSQL with connection pooling
```

## 1.3.2 The "Works on My Machine" is Actually Good

**Your projects run on**:
- Mac Mini M4 (homelab)
- OCI Always Free Tier (cloud)
- Local MacBook (development)

**This is a feature, not a bug**:
- You know these environments
- You can reproduce issues
- You can test before deploying

**ONE_SHOT should embrace this**:
- Default to "works on Ubuntu 24.04 LTS" (your homelab OS)
- Provide Mac-specific instructions when needed
- Don't try to support Windows (you don't use it)
```

---

## 🤖 THEME 3: AI Integration Philosophy

### What You Actually Do

**Cost-Conscious AI** (from Frugalos, OOS, Atlas-voice):
- **Default**: Gemini 2.5 Flash Lite via OpenRouter (~$0.10-0.30/M tokens)
- **Upgrade**: Only when Flash Lite genuinely fails
- **Reality**: Most projects cost $1-3/month in AI

**AI Use Cases** (from your projects):
1. **Content Processing** (Atlas, Divorce): Summarization, categorization, extraction
2. **Voice Analysis** (Atlas-voice): Pattern extraction, linguistic analysis
3. **Smart Routing** (Frugalos/Hermes): Model selection, cost optimization
4. **Classification** (TrojanHorse): Note categorization, tagging

**What You DON'T Do**:
- ❌ Use AI for everything
- ❌ Default to expensive models
- ❌ Build complex agent systems unless necessary
- ❌ Use AI when a regex will do

### The "Try Cheap First" Pattern

**From Frugalos/Hermes**:
```python
# Local-First AI Router pattern
1. Try local models first (Ollama - FREE)
2. If local fails, try Gemini Flash Lite ($0.10/M)
3. If Flash fails, try Claude Haiku ($0.80/M)
4. Only use Sonnet/Opus if absolutely necessary

# Transparent cost analysis
- Show single-task cost vs. full session cost
- Track costs in SQLite
- Alert when approaching budget limits
```

### ONE_SHOT Improvement

**Enhance Section 9 (AI Integration)**:
```markdown
## 9.7 The Three-Tier AI Strategy

**Tier 1: Free/Local** (try first):
- Ollama with local models (llama3.1, qwen2.5-coder)
- No cost, no latency, full privacy
- Use for: Simple tasks, iteration, experimentation

**Tier 2: Ultra-Cheap Cloud** (default for production):
- Gemini 2.5 Flash Lite via OpenRouter (~$0.10-0.30/M)
- Fast, cheap, good enough for 90% of tasks
- Use for: Summaries, categorization, simple code, Q&A

**Tier 3: Premium** (only when necessary):
- Claude Haiku/Sonnet/Opus
- Use for: Complex code, critical decisions, architecture

**Decision Tree**:
```python
def choose_model(task_type: str, complexity: str) -> str:
    # Try local first if available
    if ollama_available() and complexity == "simple":
        return "ollama/llama3.1"
    
    # Default to Flash Lite
    if complexity in ["simple", "medium"]:
        return "google/gemini-2.5-flash-lite"
    
    # Upgrade only when necessary
    if complexity == "complex" and task_type == "code":
        return "anthropic/claude-3-5-sonnet"
    
    # Last resort
    if complexity == "critical":
        return "anthropic/claude-3-opus"
    
    # Fallback
    return "google/gemini-2.5-flash-lite"
```

## 9.8 Cost Tracking (Required for AI Projects)

Every AI-enabled ONE_SHOT project should include:

```python
# ai_usage.py
import sqlite3
from datetime import datetime

class AIUsageTracker:
    def __init__(self, db_path="ai_usage.db"):
        self.db = sqlite3.connect(db_path)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS usage (
                timestamp TEXT,
                model TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                estimated_cost REAL
            )
        """)
    
    def log(self, model, input_tokens, output_tokens):
        cost = self.estimate_cost(model, input_tokens, output_tokens)
        self.db.execute(
            "INSERT INTO usage VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), model, input_tokens, output_tokens, cost)
        )
        self.db.commit()
        return cost
    
    def monthly_cost(self):
        # Return current month's total cost
        pass
```

**Add to README**:
```markdown
## 💰 AI Cost Tracking

Current month: $X.XX
Model breakdown:
- Gemini Flash Lite: $X.XX (XX% of total)
- Claude Haiku: $X.XX (XX% of total)
- Claude Sonnet: $X.XX (XX% of total)

Budget: $5/month
Status: ✅ Under budget / ⚠️ Approaching limit / ❌ Over budget
```
```

---

## 🔧 THEME 4: Operational Excellence

### What You Build Into Every Project

**Health Monitoring** (from all projects):
- `/health` endpoints for web services
- Status scripts (`.sh` files that show current state)
- Systematic debugging workflows

**Examples**:
- **Atlas**: `atlas_status.sh` - shows processing status, transcript counts, uptime
- **Homelab**: Health checks in Docker Compose, systemd monitoring
- **Divorce**: `query.py` with summary/status commands

**The Status Script Pattern**:
```bash
#!/usr/bin/env bash
# project_status.sh

echo "=== PROJECT STATUS ==="
echo "Date: $(date)"
echo ""

# Process status
if pgrep -f "project_name" > /dev/null; then
    echo "✅ Process: RUNNING"
else
    echo "❌ Process: STOPPED"
fi

# Data status
echo "📊 Records: $(sqlite3 project.db 'SELECT COUNT(*) FROM main_table')"

# Recent activity
echo "⚡ Last activity: $(sqlite3 project.db 'SELECT MAX(timestamp) FROM events')"

# Health check
if curl -sf http://localhost:8000/health > /dev/null; then
    echo "🌐 API: HEALTHY"
else
    echo "❌ API: DOWN"
fi
```

### The "Make It Observable" Pattern

**From Divorce project**:
- Web search platform with real-time statistics dashboard
- CSV export for external analysis
- Query interface with multiple views (daily, weekly, monthly)

**From Homelab**:
- Comprehensive monitoring stack
- Health checks every 15 minutes
- Automatic restart on failure

### ONE_SHOT Improvement

**Add to Section 8 (Archon Ops Patterns)**:
```markdown
## 8.4 Required Observability

Every ONE_SHOT project MUST include:

### 8.4.1 Status Command/Script

**For CLI projects**:
```bash
# Add a 'status' subcommand
project status

# Output:
# ✅ Database: Connected (1,234 records)
# ✅ Last run: 2 minutes ago
# ⚠️ Warnings: 3 items need attention
```

**For web/service projects**:
```bash
# Create project_status.sh
./project_status.sh

# Output:
# ✅ Service: RUNNING (PID: 12345, Uptime: 2d 3h)
# ✅ API: HEALTHY (http://localhost:8000/health)
# 📊 Requests: 1,234 (last hour)
# ⚠️ Errors: 5 (last hour)
```

### 8.4.2 Health Endpoint (Web Services)

```python
from fastapi import FastAPI
from datetime import datetime
import sqlite3

app = FastAPI()

@app.get("/health")
async def health():
    # Basic health
    health_status = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
    
    # Check database
    try:
        db = sqlite3.connect("project.db")
        db.execute("SELECT 1").fetchone()
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check external dependencies
    # ... add checks for APIs, file systems, etc.
    
    return health_status

@app.get("/metrics")
async def metrics():
    # Return operational metrics
    db = sqlite3.connect("project.db")
    return {
        "total_records": db.execute("SELECT COUNT(*) FROM main_table").fetchone()[0],
        "last_activity": db.execute("SELECT MAX(timestamp) FROM events").fetchone()[0],
        "errors_last_hour": db.execute(
            "SELECT COUNT(*) FROM errors WHERE timestamp > datetime('now', '-1 hour')"
        ).fetchone()[0]
    }
```

### 8.4.3 Logging Standards

```python
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/project_{datetime.now():%Y%m%d}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Log important events
logger.info("Processing started")
logger.warning("Unusual condition detected")
logger.error("Operation failed", exc_info=True)
```

**Log rotation** (add to systemd service or cron):
```bash
# Keep last 30 days of logs
find logs/ -name "*.log" -mtime +30 -delete
```
```

---

## 🎨 THEME 5: The "Real Problem" Filter

### What Makes Your Projects Different

**You build things you actually use**:
- **Divorce**: Real legal case, real data, real urgency
- **Homelab**: Real media server, real family users
- **TrojanHorse**: Real note-taking workflow
- **Atlas**: Real podcast research needs
- **Tablo**: Real TV recordings to process

**This creates natural constraints**:
- Features that don't work get fixed immediately
- Documentation that's unclear gets rewritten
- Complexity that slows you down gets simplified

### The Anti-Pattern: Tech for Tech's Sake

**What you DON'T do**:
- ❌ Build a project to learn a new framework (learning is a side effect, not the goal)
- ❌ Add features because they're cool (only add what you need)
- ❌ Use bleeding-edge tech (stable, boring tech wins)
- ❌ Build for imaginary users (you are the user)

### ONE_SHOT Improvement

**Add to Section 2 (Core Questions)**:
```markdown
## Q2.5 The Reality Check

**Before building anything, answer these**:

1. **Do you actually have this problem right now?**
   - [ ] Yes, I hit this issue weekly
   - [ ] Yes, I hit this issue monthly
   - [ ] No, but I might someday (⚠️ WARNING: Don't build it)
   - [ ] No, this is a learning project (⚠️ Mark as such in README)

2. **What's your current painful workaround?**
   ```
   [Describe what you do manually now]
   ```
   
   If you don't have a workaround, you might not have a real problem.

3. **What's the simplest thing that would help?**
   ```
   [Describe the 20% solution that gives 80% of the value]
   ```
   
   Build this first. Everything else is v2+.

4. **How will you know it's working?**
   ```
   [Observable outcome, not "it exists"]
   ```
   
   Example: "I process my weekly notes in 5 minutes instead of 30"

## Q2.6 The "Would I Use This Tomorrow?" Test

**Imagine the project is done. Tomorrow morning, you need to**:
```
[Describe a specific task you'd do with this tool]
```

**If you can't describe a specific task, stop and reconsider the project.**

**Good examples**:
- "Import my bank transactions and categorize them"
- "Find all mentions of 'custody' in my divorce communications"
- "Process this week's podcast transcripts"

**Bad examples**:
- "Explore the data"
- "Manage things better"
- "Be more organized"
```

---

## 🛠️ THEME 6: Automation Obsession

### The "Do It Twice, Script It" Pattern

**From your projects**:
- **Homelab**: `setup.sh` - complete deployment automation
- **Divorce**: `RUN_EVERYTHING.sh` - full data ingestion pipeline
- **TrojanHorse**: `start_workday.sh` - one-click workday setup
- **Atlas**: `start_atlas.sh` - automated processing startup

**The Pattern**:
```bash
#!/usr/bin/env bash
# start_project.sh - One command to rule them all

set -euo pipefail

echo "🚀 Starting project..."

# 1. Validate environment
./scripts/validate.sh || exit 1

# 2. Start dependencies
docker compose up -d

# 3. Wait for health
until curl -sf http://localhost:8000/health; do
    echo "Waiting for service..."
    sleep 2
done

# 4. Run initialization if needed
if [ ! -f ".initialized" ]; then
    ./scripts/init.sh
    touch .initialized
fi

echo "✅ Project ready!"
echo "📊 Status: http://localhost:8000/status"
```

### The "Cron-Friendly" Pattern

**From TrojanHorse**:
```bash
# Designed to run unattended
*/10 * * * * /path/to/project/scripts/process.sh >> /var/log/project.log 2>&1
```

**Requirements**:
- Exit codes (0 = success, non-zero = failure)
- Idempotent (safe to run multiple times)
- Logging to files (not just stdout)
- Lock files to prevent concurrent runs

### ONE_SHOT Improvement

**Add to Section 7 (Autonomous Execution)**:
```markdown
## 7.6 Automation Scripts (Required)

Every ONE_SHOT project MUST include:

### 7.6.1 Setup Script

```bash
#!/usr/bin/env bash
# scripts/setup.sh - Complete environment setup

set -euo pipefail

echo "=== Project Setup ==="

# 1. Check prerequisites
command -v python3 >/dev/null || { echo "❌ Python not found"; exit 1; }
command -v git >/dev/null || { echo "❌ Git not found"; exit 1; }

# 2. Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 3. Install dependencies
source venv/bin/activate
pip install -r requirements.txt

# 4. Initialize database
if [ ! -f "project.db" ]; then
    python3 -c "from project import init_db; init_db()"
fi

# 5. Create .env if missing
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  Edit .env with your configuration"
fi

echo "✅ Setup complete!"
```

### 7.6.2 Start Script

```bash
#!/usr/bin/env bash
# scripts/start.sh - Start the project

set -euo pipefail

# Activate environment
source venv/bin/activate

# Check health of dependencies
./scripts/healthcheck.sh || exit 1

# Start the service
if [ -f "project.pid" ]; then
    echo "⚠️  Project already running (PID: $(cat project.pid))"
    exit 1
fi

# Run in background
nohup python3 -m project.main > logs/project.log 2>&1 &
echo $! > project.pid

echo "✅ Project started (PID: $!)"
```

### 7.6.3 Stop Script

```bash
#!/usr/bin/env bash
# scripts/stop.sh - Stop the project

set -euo pipefail

if [ ! -f "project.pid" ]; then
    echo "⚠️  Project not running"
    exit 0
fi

PID=$(cat project.pid)
if kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    rm project.pid
    echo "✅ Project stopped"
else
    echo "⚠️  Process not found, cleaning up"
    rm project.pid
fi
```

### 7.6.4 Cron-Friendly Process Script

```bash
#!/usr/bin/env bash
# scripts/process.sh - Run processing (cron-safe)

set -euo pipefail

# Lock file to prevent concurrent runs
LOCKFILE="/tmp/project.lock"
if [ -f "$LOCKFILE" ]; then
    echo "Already running, exiting"
    exit 0
fi

trap "rm -f $LOCKFILE" EXIT
touch "$LOCKFILE"

# Activate environment
cd "$(dirname "$0")/.."
source venv/bin/activate

# Run processing
python3 -m project.process

# Exit code determines cron success/failure
exit $?
```

**Add to crontab**:
```bash
# Run every 10 minutes
*/10 * * * * /path/to/project/scripts/process.sh >> /var/log/project.log 2>&1
```
```

---

## 🧠 THEME 7: The "Future-You" Mindset

### What This Means in Practice

**From your projects, you consistently**:
- Write READMEs that explain context, not just commands
- Add troubleshooting sections based on actual issues you hit
- Document WHY decisions were made
- Create status/health scripts so future-you can diagnose issues
- Use descriptive variable/function names (no `x`, `tmp`, `data`)

**Examples**:
- **Homelab**: "You're here because the OptiPlex is arriving in 3 days and you need to know exactly what to do"
- **Divorce**: Multiple "COMPLETE" status files documenting what was done and why
- **OOS**: Extensive documentation of lessons learned, anti-patterns to avoid

### The "Explain to Yourself in 6 Months" Pattern

**Good documentation** (from your projects):
```markdown
## Why SQLite Instead of PostgreSQL?

We chose SQLite because:
1. Single-file database (easy backup/restore)
2. No server to manage
3. Handles our 135K records with sub-second queries
4. Can upgrade to Postgres if we hit limits

**Upgrade trigger**: > 100K records OR need multi-user access

**Current status**: 135K records, queries < 1s, no issues
```

**Bad documentation** (what you avoid):
```markdown
## Database

Uses SQLite.
```

### ONE_SHOT Improvement

**Add to Section 1.2 (Archon Principles)**:
```markdown
## 1.2.5 Future-You Documentation

**Every non-obvious decision needs a WHY comment or doc section.**

### In Code

```python
# Good: Explains WHY
# Using SQLite instead of Postgres because:
# 1. Single-file portability (easy backup)
# 2. No server overhead
# 3. Handles our 100K records fine
# Will upgrade to Postgres if we hit 500K records or need multi-user
db = sqlite3.connect("project.db")

# Bad: Just states WHAT
db = sqlite3.connect("project.db")
```

### In README

**Required sections**:
1. **Architecture Decisions** - Why this stack?
2. **Upgrade Triggers** - When to change tech?
3. **Known Limitations** - What doesn't this do?
4. **Troubleshooting** - Issues you've actually hit

**Template**:
```markdown
## Architecture Decisions

### Why SQLite?
- Single-file portability
- No server overhead
- Sufficient for < 500K records
- **Upgrade trigger**: > 500K records OR multi-user needed

### Why FastAPI?
- Modern async support
- Auto-generated API docs
- Type hints for validation
- **Alternative**: Flask if you need simpler/more mature

### Why Tailscale?
- Zero-config VPN
- No port forwarding
- Free tier sufficient
- **Alternative**: WireGuard if you want more control

## Known Limitations

- Single-user only (no auth system)
- No real-time updates (polling only)
- No mobile app (web UI only)

## Troubleshooting

### "Database is locked"
**Cause**: Multiple processes accessing SQLite  
**Fix**: Close other connections, or upgrade to Postgres

### "Service won't start"
**Cause**: Port 8000 already in use  
**Fix**: `lsof -i :8000` to find process, kill it or change port
```
```

---

## 📊 THEME 8: Data-Centric Design

### The Pattern Across Projects

**You build around data, not features**:
- **Divorce**: 135K records, multiple data sources, comprehensive schema
- **Atlas**: 750 transcripts, structured metadata, searchable database
- **TrojanHorse**: Notes → structured knowledge, YAML frontmatter
- **Homelab**: Configuration as data (docker-compose.yml, .env)

**Data First, UI Second**:
1. Define data models (what you're storing)
2. Build storage layer (how you're storing it)
3. Build processing (how you transform it)
4. Build interface (how you access it)

**Not**:
1. ~~Build UI mockups~~
2. ~~Figure out data later~~

### The "Show Me the Schema" Pattern

**From Divorce project**:
```sql
-- Complete schema upfront
CREATE TABLE communications (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    from_identifier TEXT,
    to_identifier TEXT,
    subject TEXT,
    body_text TEXT,
    source_type TEXT,  -- 'text', 'email', 'imessage'
    legal_relevance TEXT,  -- 'critical', 'high', 'medium', 'low'
    ...
);

-- Multiple views for different access patterns
CREATE VIEW communications_by_month AS ...
CREATE VIEW communications_by_day AS ...
CREATE VIEW high_priority_evidence AS ...
```

**This enables**:
- Clear understanding of what data exists
- Multiple access patterns without code changes
- Easy export/analysis
- Future-proof schema evolution

### ONE_SHOT Improvement

**Add to Section 7.2 (Phase 1: Core Implementation)**:
```markdown
## 7.2.1 Data-First Implementation Order

**Step 1: Define Data Models**

Create `models.py` (or equivalent) with complete data structures:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Transaction:
    """Financial transaction.
    
    This is the core data type for the entire project.
    Everything else is built around transforming/querying these.
    """
    id: str
    timestamp: datetime
    description: str
    amount: float
    category: Optional[str] = None
    account: str = "checking"
    
    def to_dict(self) -> dict:
        """For JSON serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "amount": self.amount,
            "category": self.category,
            "account": self.account
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        """For JSON deserialization."""
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            description=data["description"],
            amount=data["amount"],
            category=data.get("category"),
            account=data.get("account", "checking")
        )
```

**Step 2: Define Storage Schema**

For SQLite/PostgreSQL:

```sql
-- schema.sql
-- Complete schema with comments explaining each field

CREATE TABLE transactions (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,  -- ISO 8601 format
    description TEXT NOT NULL,
    amount REAL NOT NULL,  -- Negative for expenses, positive for income
    category TEXT,  -- NULL until categorized
    account TEXT DEFAULT 'checking',
    
    -- Metadata
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_timestamp ON transactions(timestamp);
CREATE INDEX idx_category ON transactions(category);
CREATE INDEX idx_account ON transactions(account);

-- Views for common access patterns
CREATE VIEW monthly_summary AS
SELECT 
    strftime('%Y-%m', timestamp) as month,
    category,
    SUM(amount) as total,
    COUNT(*) as count
FROM transactions
GROUP BY month, category;

CREATE VIEW uncategorized AS
SELECT * FROM transactions WHERE category IS NULL;
```

**Step 3: Implement Storage Layer**

```python
# storage.py
import sqlite3
from typing import List, Optional
from .models import Transaction

class TransactionStore:
    """Storage layer for transactions.
    
    All database access goes through this class.
    Makes it easy to swap storage backends later.
    """
    
    def __init__(self, db_path: str = "transactions.db"):
        self.db = sqlite3.connect(db_path)
        self._init_schema()
    
    def _init_schema(self):
        """Initialize database schema."""
        with open("schema.sql") as f:
            self.db.executescript(f.read())
    
    def add(self, transaction: Transaction) -> None:
        """Add a transaction."""
        self.db.execute(
            """INSERT INTO transactions 
               (id, timestamp, description, amount, category, account)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                transaction.id,
                transaction.timestamp.isoformat(),
                transaction.description,
                transaction.amount,
                transaction.category,
                transaction.account
            )
        )
        self.db.commit()
    
    def get(self, id: str) -> Optional[Transaction]:
        """Get a transaction by ID."""
        row = self.db.execute(
            "SELECT * FROM transactions WHERE id = ?", (id,)
        ).fetchone()
        
        if not row:
            return None
        
        return Transaction(
            id=row[0],
            timestamp=datetime.fromisoformat(row[1]),
            description=row[2],
            amount=row[3],
            category=row[4],
            account=row[5]
        )
    
    def list(self, limit: int = 100) -> List[Transaction]:
        """List recent transactions."""
        rows = self.db.execute(
            "SELECT * FROM transactions ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        ).fetchall()
        
        return [Transaction(...) for row in rows]
    
    # ... more methods
```

**Step 4: Build Processing**

```python
# processor.py
from .storage import TransactionStore
from .models import Transaction

class TransactionProcessor:
    """Business logic for transactions."""
    
    def __init__(self, store: TransactionStore):
        self.store = store
    
    def import_csv(self, path: str) -> int:
        """Import transactions from CSV."""
        count = 0
        # ... CSV parsing logic
        return count
    
    def categorize(self, transaction: Transaction) -> str:
        """Auto-categorize a transaction."""
        # ... categorization logic
        pass
```

**Step 5: Build Interface (Last)**

```python
# cli.py
import click
from .storage import TransactionStore
from .processor import TransactionProcessor

@click.group()
def cli():
    """Transaction manager."""
    pass

@cli.command()
@click.argument('path')
def import_csv(path):
    """Import transactions from CSV."""
    store = TransactionStore()
    processor = TransactionProcessor(store)
    count = processor.import_csv(path)
    click.echo(f"✅ Imported {count} transactions")

# ... more commands
```

**Why This Order?**

1. **Data models** = contract for the entire project
2. **Storage schema** = how data persists
3. **Storage layer** = abstraction over database
4. **Processing** = business logic
5. **Interface** = how users interact

**Benefits**:
- Can test storage without UI
- Can swap storage backends (SQLite → Postgres)
- Can add multiple interfaces (CLI + web + API)
- Clear separation of concerns
```

---

## 🚫 ANTI-PATTERNS: What You've Learned NOT to Do

### From OOS Project

**Lesson**: Complexity for complexity's sake

**What happened**:
- Built overly complex command generator (1,363 lines)
- Replaced with simple handler (104 lines)
- Same functionality, 92% less code

**The Learning**:
> "Recently simplified by 27.5% (1,794 lines removed): Replaced overly complex 1,363-line command_generator.py with clean 104-line simple_command_handler.py"

### From Multiple Projects

**Anti-Pattern**: Building before validating

**Better Pattern** (from Homelab):
```bash
# Always validate environment first
./scripts/validate.sh || exit 1

# Then build
./scripts/setup.sh
```

### From Divorce Project

**Anti-Pattern**: Assuming data is clean

**Better Pattern**:
- Validate data integrity upfront
- Document data sources and checksums
- Build verification scripts

### ONE_SHOT Improvement

**Add new section**:
```markdown
# 14. ANTI-PATTERNS (Learn from Past Mistakes)

## 14.1 Complexity Creep

**Anti-Pattern**: Adding abstraction layers "for flexibility"

**Example**:
```python
# Bad: Over-engineered
class AbstractDataProviderFactory:
    def create_provider(self, provider_type: str) -> AbstractDataProvider:
        ...

# Good: Simple and direct
def get_data(source: str) -> dict:
    if source.endswith('.json'):
        return json.load(open(source))
    elif source.endswith('.yaml'):
        return yaml.safe_load(open(source))
    else:
        raise ValueError(f"Unknown format: {source}")
```

**Rule**: Only add abstraction when you have 3+ implementations, not "in case we need it later"

## 14.2 Building Before Validating

**Anti-Pattern**: Start coding immediately

**Better Pattern**:
```bash
# Phase 0: Validate (ALWAYS)
1. Check environment (Python version, dependencies)
2. Check connectivity (database, APIs, file access)
3. Check data (does input exist? is it valid?)

# Phase 1: Build (ONLY AFTER VALIDATION)
4. Implement core logic
5. Add tests
6. Deploy
```

**Template validation script**:
```bash
#!/usr/bin/env bash
# scripts/validate.sh

set -euo pipefail

echo "=== Environment Validation ==="

# Check Python
python3 --version || { echo "❌ Python not found"; exit 1; }

# Check dependencies
command -v git >/dev/null || { echo "❌ Git not found"; exit 1; }

# Check data sources
[ -f "data/input.csv" ] || { echo "❌ Input data not found"; exit 1; }

# Check connectivity
curl -sf https://api.example.com/health || { echo "❌ API unreachable"; exit 1; }

echo "✅ All checks passed"
```

## 14.3 Assuming Data is Clean

**Anti-Pattern**: Process data without validation

**Better Pattern**:
```python
def import_data(path: str) -> int:
    # Validate before processing
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")
    
    # Check file size (avoid loading huge files into memory)
    size_mb = os.path.getsize(path) / 1024 / 1024
    if size_mb > 100:
        raise ValueError(f"File too large: {size_mb:.1f}MB (max 100MB)")
    
    # Validate format
    with open(path) as f:
        first_line = f.readline()
        if not first_line.startswith("id,timestamp,"):
            raise ValueError("Invalid CSV format (missing expected headers)")
    
    # Now process
    count = 0
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Validate each row
            if not row.get('id'):
                logger.warning(f"Skipping row with missing ID: {row}")
                continue
            
            # Process valid row
            process_row(row)
            count += 1
    
    return count
```

## 14.4 No Rollback Plan

**Anti-Pattern**: Deploy without ability to undo

**Better Pattern**:
```bash
# Before deployment
1. Backup database: ./scripts/backup.sh
2. Tag current version: git tag v1.2.3
3. Deploy new version
4. Test health endpoint
5. If failed: ./scripts/rollback.sh

# scripts/rollback.sh
#!/usr/bin/env bash
set -euo pipefail

echo "⚠️  Rolling back to previous version"

# Stop current version
./scripts/stop.sh

# Restore backup
cp backups/project.db.backup project.db

# Checkout previous version
git checkout v1.2.2

# Restart
./scripts/start.sh

echo "✅ Rollback complete"
```

## 14.5 Ignoring Error Cases

**Anti-Pattern**: Only handle happy path

**Better Pattern**:
```python
def process_item(item: dict) -> bool:
    """Process an item.
    
    Returns True if successful, False otherwise.
    Logs errors but doesn't crash.
    """
    try:
        # Validate input
        if not item.get('id'):
            logger.error(f"Item missing ID: {item}")
            return False
        
        # Process
        result = do_processing(item)
        
        # Validate output
        if not result:
            logger.warning(f"Processing returned empty result for {item['id']}")
            return False
        
        return True
        
    except KeyError as e:
        logger.error(f"Missing required field: {e}", exc_info=True)
        return False
    except ValueError as e:
        logger.error(f"Invalid value: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Unexpected error processing {item.get('id')}: {e}", exc_info=True)
        return False
```
```

---

## 🎯 ACTIONABLE RECOMMENDATIONS

### Immediate Changes to ONE_SHOT

1. **Add "Reality Check" questions** (Section 2.5, 2.6)
   - Force validation of actual need
   - Prevent building solutions looking for problems

2. **Enhance AI cost guidance** (Section 9.7, 9.8)
   - Three-tier strategy (local → cheap → premium)
   - Required cost tracking for AI projects

3. **Add automation requirements** (Section 7.6)
   - Setup, start, stop, process scripts
   - Cron-friendly patterns

4. **Require observability** (Section 8.4)
   - Status scripts/commands
   - Health endpoints
   - Metrics endpoints

5. **Add anti-patterns section** (Section 14)
   - Document what NOT to do
   - Learn from past mistakes

6. **Strengthen data-first approach** (Section 7.2.1)
   - Models → Schema → Storage → Processing → Interface
   - Clear implementation order

7. **Add "Future-You" documentation requirements** (Section 1.2.5)
   - WHY comments in code
   - Architecture decisions in README
   - Upgrade triggers documented

### Philosophy Refinements

**Current ONE_SHOT says**: "Simplicity First"

**Your projects show**: "Simplicity Through Real-World Use"

**Refined principle**:
> Build the simplest thing that solves YOUR actual problem TODAY. Document when to upgrade. Let real usage drive complexity, not imagined future needs.

**Current ONE_SHOT says**: "AI is optional"

**Your projects show**: "AI is cheap if you're smart about it"

**Refined principle**:
> AI costs $1-3/month if you default to cheap models and upgrade only when necessary. Track costs, show upgrade decisions, make it transparent.

**Current ONE_SHOT says**: "FOSS where possible"

**Your projects show**: "FOSS with pragmatic exceptions"

**Refined principle**:
> Use FOSS for infrastructure (Docker, Nginx, PostgreSQL). Use paid APIs for AI (cheaper than self-hosting). Document the tradeoff.

---

## 🎓 META-LESSONS

### What Makes Your Projects Successful

1. **You use them** - Real problems create real constraints
2. **You document for future-you** - 6 months later, you can still understand it
3. **You automate ruthlessly** - Do it twice, script it
4. **You start simple** - SQLite before Postgres, files before databases
5. **You make it observable** - Status scripts, health checks, logs
6. **You track costs** - Especially for AI, make spending visible
7. **You avoid complexity** - 104 lines beats 1,363 lines

### The Connecting Thread

**You're building a personal infrastructure**:
- Homelab (physical infrastructure)
- OOS (development infrastructure)
- TrojanHorse (knowledge infrastructure)
- Atlas (research infrastructure)
- Divorce (legal infrastructure)

**Each project**:
- Solves a real problem
- Integrates with others (APIs, data formats)
- Is documented for future-you
- Can run unattended
- Has observable health

**This is the ethos**: Build tools that work together, document them well, automate everything, keep it simple.

---

## 🚀 NEXT STEPS

### For ONE_SHOT v1.5

1. **Integrate all recommendations above**
2. **Add examples from your projects**
   - Use Divorce as example of data-centric design
   - Use Homelab as example of deployment automation
   - Use OOS as example of complexity reduction
3. **Create project templates**
   - CLI tool template (based on TrojanHorse)
   - Web app template (based on Atlas)
   - Data pipeline template (based on Divorce)
4. **Add validation checklist**
   - Before starting any project
   - After completing any project

### For Your Next Project

**Use ONE_SHOT as-is, but with these additions**:
1. Answer the "Reality Check" questions honestly
2. Start with data models, not features
3. Build automation scripts from day 1
4. Track AI costs if using AI
5. Document WHY for non-obvious decisions
6. Create status script early

---

## 📝 APPENDIX: Project Summaries

### Atlas
**Type**: Data pipeline + API  
**Purpose**: Podcast transcript discovery and processing  
**Key Patterns**: Status scripts, API integration, systematic processing  
**Scale**: 750 transcripts, 2,373 episodes tracked  

### Atlas-voice
**Type**: Data processing + AI  
**Purpose**: Voice pattern analysis for AI prompts  
**Key Patterns**: Privacy-first architecture, nuclear safe room pattern, corpus analysis  
**Scale**: 104M+ character corpus  

### Divorce
**Type**: Data pipeline + web search  
**Purpose**: Legal discovery database  
**Key Patterns**: Comprehensive schema, multiple data sources, web RAG platform  
**Scale**: 135K records, 4,232 days coverage  

### Frugalos/Hermes
**Type**: AI assistant system  
**Purpose**: Backend-agnostic AI with cost optimization  
**Key Patterns**: Local-first routing, cost tracking, transparent upgrade decisions  
**Scale**: Production-ready with monitoring  

### Homelab
**Type**: Infrastructure deployment  
**Purpose**: Self-hosted media/services  
**Key Patterns**: Docker Compose modular includes, comprehensive documentation, step-by-step deployment  
**Scale**: 29 services, complete automation  

### Tablo
**Type**: Data pipeline  
**Purpose**: TV recording automation  
**Key Patterns**: Direct drive mode, dual mode support, AI identification  
**Scale**: Weekly processing automation  

### TrojanHorse
**Type**: Knowledge management  
**Purpose**: Note processing and RAG search  
**Key Patterns**: Local-first, AI classification, workday automation  
**Scale**: Continuous processing, multi-device  

### VDD/OOS
**Type**: Development framework  
**Purpose**: Context engineering for AI development  
**Key Patterns**: Token optimization, meta-clarification, simplification (27.5% code reduction)  
**Scale**: Production-ready, comprehensive testing  

---

**END OF ANALYSIS**

This document represents the distilled wisdom from your development work. Use it to refine ONE_SHOT into a framework that captures not just what you build, but HOW and WHY you build it.
