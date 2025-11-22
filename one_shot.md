# ONE_SHOT: AI-Powered Autonomous Project Builder

**Version**: 1.2
**Philosophy**: Ask everything upfront, then execute autonomously
**Target**: OCI Always Free Tier + Tailscale + GitHub
**Cost**: $0/month forever
**Core Principles**: Validate Before Create, Dependency Awareness, WHY documentation

---

## HOW THIS WORKS

This single file is your complete project builder. Here's the workflow:

```
1. INTERACTIVE PHASE (5-15 minutes, you + Claude)
   ├─ Answer project questions
   ├─ Validate connections (GitHub, Tailscale)
   ├─ Make all architectural decisions
   └─ Generate complete PRD

2. AUTONOMOUS PHASE (hours to days, Claude Code alone)
   ├─ Create repo structure
   ├─ Implement all features
   ├─ Write tests
   ├─ Commit + push automatically
   └─ Deploy to Tailscale HTTPS

3. DONE
   └─ Working project at https://[project].deer-panga.ts.net
```

**You answer questions once. Claude Code does the rest.**

---

## STEP 1: INTERACTIVE SETUP

### Current Environment Check

**VM Details**:
- Host: `oci-dev-public` (SSH alias)
- Tailnet: `deer-panga.ts.net`
- Tailscale name: `oci-dev`
- Python: 3.12 (assumed installed)

**Let's validate connections...**

Run these commands on your VM:

```bash
# Check Python
python3 --version

# Check git + GitHub auth
git config --global user.name
git config --global user.email
gh auth status  # or just try: git ls-remote https://github.com/yourusername/test.git

# Check Tailscale
tailscale status | grep deer-panga

# Check if logged into GitHub CLI (optional but helpful)
gh auth status
```

**Paste results here, or just confirm:**
- [ ] Python 3.11+ installed
- [ ] Git configured with your name/email
- [ ] GitHub authentication works (SSH or HTTPS)
- [ ] Tailscale connected to deer-panga.ts.net
- [ ] SSH to oci-dev-public works

---

### PROJECT QUESTIONNAIRE

**I'll ask you questions to generate the complete PRD. Answer each one.**

#### Core Project Definition

**Q1: What are you building?**
(One sentence: "A tool that does X for Y people")

**Example**: "A personal knowledge manager that converts newsletters/podcasts into searchable YAML files for developers who consume lots of content"

**Your answer**:
```
[YOUR ANSWER HERE]
```

---

**Q2: What's the core problem this solves?**
(Why does this need to exist? What's painful without it?)

**Your answer**:
```
[YOUR ANSWER HERE]
```

---

**Q3: What's your philosophy for this project?**
(3-5 bullet points - these guide ALL decisions)

**Example**:
- Simplicity over features
- Local-first, no cloud dependencies
- CLI-only, no web UI needed
- < 300 lines per module
- Works offline

**Your answer**:
```
[YOUR ANSWER HERE]
```

---

#### Project Scope

**Q4: What will this project DO?** 
(List 3-7 concrete features, be specific)

**Example**:
1. Import newsletter from URL, save as YAML
2. Extract podcast transcript, save as YAML  
3. Search all content by keyword
4. Export filtered content as markdown
5. CLI with simple commands

**Your answer**:
```
1. [FEATURE 1]
2. [FEATURE 2]
3. [FEATURE 3]
4. [etc...]
```

---

**Q5: What will this project NOT do?**
(Explicitly exclude things to prevent scope creep)

**Example**:
- No web interface (CLI only)
- No real-time sync (batch processing)
- No multi-user support (single user)
- No AI processing (just storage/search)

**Your answer**:
```
[YOUR ANSWER HERE]
```

---

**Q6: What type of project is this?**
(Pick one - affects structure and patterns)

- [ ] A. CLI Tool (commands, flags, local execution)
- [ ] B. Python Library (importable, reusable functions)
- [ ] C. Web Application (FastAPI, frontend, database)
- [ ] D. Data Pipeline (ETL, scheduled jobs, transformations)
- [ ] E. Background Service (runs 24/7, monitoring, alerts)

**Your choice**: [LETTER]

---

#### Data & Storage

**Q7: What data does this project work with?**
(Give me an example of each data type)

**Example**:
```yaml
# Newsletter content
type: newsletter
title: "Weekly AI Digest #42"
url: "https://example.com/digest/42"
content: "Full text of newsletter..."
published: 2024-10-01
word_count: 3420
```

**Your data examples**:
```
[PASTE EXAMPLE DATA HERE]
```

---

**Q8: How much data will this handle?**

- [ ] A. Small (< 1000 items, < 1GB)
- [ ] B. Medium (1K-100K items, 1-10GB)
- [ ] C. Large (100K+ items, 10GB+)

**Your choice**: [LETTER]

---

**Q9: Where should data be stored?**

- [ ] A. Local files (YAML/JSON in directories)
- [ ] B. SQLite database (single file DB)
- [ ] C. PostgreSQL (needs setup)
- [ ] D. Mix (files for raw, SQLite for processed)

**Your choice**: [LETTER]

**If files, what format?**
- [ ] YAML (human-readable, comments)
- [ ] JSON (standard, parseable)
- [ ] CSV (tabular data)
- [ ] Other: [specify]

---

#### External Dependencies

**Q10: Does this project need external APIs?**

- [ ] No external APIs (all local)
- [ ] Yes, free APIs (list them):
  ```
  - API 1: [name, what for, free tier limits]
  - API 2: [name, what for, free tier limits]
  ```

**If yes, do you already have API keys?**
- [ ] Yes, I'll provide them as environment variables
- [ ] No, I'll get them during setup
- [ ] No API keys needed (public APIs)

---

**Q11: What Python packages does this need?**
(Or say "you decide" and I'll pick minimal dependencies)

**Example**:
```
pyyaml - YAML parsing
click - CLI framework  
requests - HTTP calls
pytest - testing
```

**Your answer**:
```
[LIST PACKAGES OR "you decide"]
```

---

#### User Interface

**Q12: How will users interact with this?**

If CLI tool:
```bash
# What commands should exist?
project init
project import [source]
project search [query]
project export [filter]
```

If web app:
```
# What pages/routes?
/ - Homepage
/dashboard - Main interface
/api/items - REST API
```

If library:
```python
# What's the main API?
from project import Parser
parser = Parser()
data = parser.process(input)
```

**Your interface design**:
```
[PASTE YOUR COMMANDS/ROUTES/API HERE]
```

---

#### Success Criteria

**Q13: What does "done" look like?**
(How do you know this project is complete and working?)

**Example**:
- Can import 100 newsletters without errors
- Can search and find content in < 1 second
- All tests passing
- CLI help shows all commands
- Running on Tailscale HTTPS at https://project.deer-panga.ts.net

**Your success criteria**:
```
[YOUR ANSWER HERE]
```

---

**Q14: What's a "good enough" first version?**
(What's the 80% solution you'd actually use?)

**Example**:
- Import newsletters (skip podcasts for v1)
- Basic search (full-text, no fuzzy)
- Manual export (no auto-sync)
- CLI only (web later)

**Your v1 scope**:
```
[YOUR ANSWER HERE]
```

---

### Technical Decisions

**Q15: Naming**

**Project name** (lowercase, hyphens ok): [name]
**GitHub repo name** (same as project name usually): [name]
**Module name** (Python import name, no hyphens): [name]

**Example**:
- Project: "newsletter-archive"
- Repo: "newsletter-archive"  
- Module: "newsletter_archive"

**Your names**:
- Project: [YOUR PROJECT NAME]
- Repo: [YOUR REPO NAME]
- Module: [YOUR MODULE NAME]

---

**Q16: Directory Structure Preference**

- [ ] A. Flat (src/ with all .py files)
- [ ] B. Modular (src/module1/, src/module2/)
- [ ] C. Domain-driven (src/models/, src/services/, src/api/)
- [ ] D. You decide based on project type

**Your choice**: [LETTER]

---

**Q17: Testing Strategy**

- [ ] A. Minimal (test critical paths only)
- [ ] B. Thorough (aim for 80%+ coverage)
- [ ] C. Comprehensive (test everything, 100% coverage)
- [ ] D. You decide based on complexity

**Your choice**: [LETTER]

---

**Q18: Deployment Preference**

- [ ] A. Local dev only (no deployment needed)
- [ ] B. Tailscale HTTPS (https://[project].deer-panga.ts.net)
- [ ] C. Systemd service (runs 24/7 on OCI VM)
- [ ] D. Both Tailscale + systemd

**Your choice**: [LETTER]

---

### Environment Variables / Secrets

**Q19: Does this project need secrets?**

- [ ] No secrets needed
- [ ] Yes, list them:
  ```
  SECRET_NAME_1=description of what this is
  SECRET_NAME_2=description of what this is
  ```

**Will you provide these now or later?**
- [ ] Now (I'll paste them)
- [ ] Later (I'll add to .env before running)

---

### Final Confirmation

**Q20: Review and confirm**

Based on your answers, here's what I'll build:

**Project**: [name from Q15]
**Type**: [type from Q6]
**Philosophy**: [bullets from Q3]

**Features**:
[list from Q4]

**Storage**: [choice from Q9]
**Interface**: [CLI/Web/Library from Q12]
**Deployment**: [choice from Q18]

**Dependencies**:
- Python 3.12
- [packages from Q11 or minimal set I choose]
- No external paid services

**Success looks like**:
[criteria from Q13]

**Is this correct?**
- [ ] Yes, build this exactly
- [ ] No, let me change: [what to change]

---

## STEP 2: CONNECTION VALIDATION

**I'll validate your environment before building anything.**

### Archon Methodology: Validate Before Create

Run this validation script on `oci-dev-public`:

```bash
#!/bin/bash
# Save as validate.sh and run: bash validate.sh

echo "=== Environment Validation ==="

# Python version
python3 --version || echo "❌ Python not found"

# Git config
git config user.name || echo "❌ Git user.name not set"
git config user.email || echo "❌ Git user.email not set"

# GitHub access (test by listing repos)
gh repo list --limit 1 2>/dev/null || git ls-remote https://github.com/$(git config user.name)/test.git 2>/dev/null || echo "❌ GitHub auth failed"

# Tailscale
tailscale status | grep -q "deer-panga" && echo "✅ Tailscale connected" || echo "❌ Tailscale not connected"

# Disk space
df -h / | grep -v Filesystem

# Memory
free -h

echo ""
echo "=== Validation Complete ==="
```

**Paste the output here**:
```
[VALIDATION OUTPUT]
```

**Or just confirm all passed**:
- [ ] All checks passed, ready to build

---

## STEP 3: PRD GENERATION

**Based on your answers, I'll generate the complete PRD.**

This PRD will include:
1. Project overview (from Q1-Q3)
2. Features (from Q4)
3. Non-goals (from Q5)
4. Data models (from Q7, expanded)
5. Storage structure (from Q9)
6. Dependencies (from Q11)
7. CLI/API design (from Q12)
8. Error handling (auto-generated)
9. Testing strategy (from Q17)
10. Deployment plan (from Q18)

**I'll show you the PRD for final approval.**

---

## STEP 4: AUTONOMOUS EXECUTION

**After you approve the PRD, here's what happens automatically:**

### Phase 0: Setup (5 min)
- Create GitHub repo: `https://github.com/[your-username]/[repo-name]`
- Clone to VM: `~/[project-name]`
- Initialize project structure
- Set up git hooks for auto-commit
- Configure Tailscale cert (if deployment chosen)

### Phase 1: Core Implementation (30min - 6hrs depending on complexity)
- Implement data models
- Build storage layer
- Add validation logic
- Create CLI/API (based on project type)
- Write unit tests

### Archon Integration (if applicable)
- Set up Caddy for SSL/reverse proxy (if web service)
- Implement microservices communication (HTTP APIs only)
- Add health endpoints (`/health`) for all services
- Set up proper logging and error handling

### Phase 2: Integration (1-3hrs)
- End-to-end workflows
- Integration tests
- Error handling
- Logging

### Phase 3: Deployment (30min)
- Set up systemd service (if chosen)
- Configure Tailscale HTTPS (if chosen)
- Create README with usage
- Final testing

### Caddy/Web Configuration (if applicable)
```
# Add domain to /etc/caddy/Caddyfile
your-project.ts.net {
    reverse_proxy localhost:8080
    encode gzip
}
# Validate: sudo caddy validate --config /etc/caddy/Caddyfile
# Reload: sudo systemctl reload caddy
```

### Phase 4: Validation (15min)
- Run all tests
- Verify deployment
- Check GitHub repo
- Confirm Tailscale URL works

**Claude Code will show progress every 5-10 tasks and commit after each working piece.**

**You can check progress anytime**:
```bash
ssh oci-dev-public
cd ~/[project-name]
git log --oneline  # See what's been built
pytest             # Run tests
```

---

## STEP 5: HANDOFF

**When complete, you'll get:**

1. **GitHub repo**: `https://github.com/[username]/[repo-name]`
   - Complete source code
   - Tests
   - README with usage instructions
   - Git history showing build process

2. **Running project** (if deployed):
   - Tailscale URL: `https://[project].deer-panga.ts.net`
   - Systemd service (if chosen): `sudo systemctl status [project]`

3. **Documentation**:
   - README.md with installation and usage
   - ARCHITECTURE.md explaining design decisions (WHY not just HOW)
   - API.md (if library/web app)

4. **Operations Guide**:
   ```bash
   # Standard Archon workflow
   git add . && git commit -m "description" && git push
   docker compose up --build -d  # if containerized
   make dev  # if Makefile exists
   ```

5. **Troubleshooting Principles**:
   - Isolate Layer → Check Dependencies → Analyze Logs → Verify Health
   - Always check `/health` endpoints before debugging code
   - Use systematic debugging patterns

4. **Next steps guide**:
   - How to extend
   - How to deploy elsewhere
   - How to contribute

---

## READY TO START?

**Once you've answered all questions above and validated connections, tell me:**

```
I've answered all questions. Validation passed. Generate PRD and show me for approval.
```

**I'll create the complete PRD based on your answers.**

**After you approve it, I'll say:**

```
PRD approved. Execute autonomous build.
```

**Then I'll build the entire project while you go do other things.**

### Archon Workflow Integration

**Standard commands you'll see during build:**
- `docker compose up --build -d` (if containerized)
- `make dev` (if Makefile exists)
- `git add . && git commit -m 'description' && git push` (after each milestone)

**Core principles applied:**
- Document the WHY, not just the HOW
- Single responsibility for each module
- Dependency awareness and circular prevention

---

## EXAMPLE WALKTHROUGH

**To show you how this works, here's a condensed example:**

### User Answers

Q1: "A personal finance tracker that imports transactions from CSV and categorizes spending"
Q2: "Mint.com is shutting down, need free alternative for tracking spending"
Q3: 
- Local-first (no cloud)
- Privacy-focused (data never leaves machine)
- Simple CSV in/out
- CLI only

Q4:
1. Import transactions from bank CSV
2. Auto-categorize transactions
3. Generate spending reports
4. Export filtered transactions

Q5: 
- No bank API integration (manual CSV only)
- No mobile app
- No multi-currency

Q6: A (CLI Tool)

Q7:
```yaml
transaction:
  date: 2024-01-15
  description: "AMAZON.COM"
  amount: -42.99
  category: shopping
  account: checking
```

Q8: A (< 1000 transactions)
Q9: B (SQLite)
Q11: "you decide"
Q12:
```bash
finance import transactions.csv
finance categorize
finance report --month 2024-01
finance export --category food
```

Q13:
- Can import 1000 transactions in < 5 seconds
- Auto-categorizes 80%+ correctly
- Reports show spending by category
- All tests passing

Q14:
- Import + manual categorization only
- Skip auto-categorize for v1
- Basic reports only

Q15:
- Project: finance-tracker
- Repo: finance-tracker
- Module: finance_tracker

Q17: B (Thorough)
Q18: A (Local only)

**Validation**: All passed

### Generated PRD (Condensed)

```markdown
# Finance Tracker PRD

## Overview
Local-first personal finance tracker for CSV transaction management.

## Philosophy
- Local-first, no cloud
- Privacy-focused
- Simple CSV in/out
- CLI only

## Features
1. Import from CSV → SQLite
2. Manual categorization
3. Spending reports
4. Filtered exports

## Data Model
[Complete schema with examples]

## Storage
SQLite database: `~/.finance-tracker/transactions.db`

## CLI Commands
[All commands with full specifications]

## Testing
Aim for 80% coverage, focus on import/export

## Success Criteria
- Import 1000 transactions < 5s
- All tests passing
- CLI help functional
```

### Autonomous Build

**Phase 0**: Create repo, clone, structure ✅
**Phase 1**: Data models, SQLite, CLI skeleton ✅
**Phase 2**: Import/export, tests ✅
**Phase 3**: Reports, documentation ✅

**Result**: Working finance tracker at `~/finance-tracker`, all code on GitHub

---

## PHILOSOPHY OF ONE_SHOT + ARCHON INTEGRATION

This file embodies a specific philosophy enhanced with Archon principles:

### Front-Load All Decisions
- No "we'll figure it out later"
- No "TBD" or "TODO"
- All architectural decisions made upfront
- All questions asked before building

### Document the WHY, Not Just the HOW
- WHY this database choice (not just HOW to use it)
- WHY this architecture pattern (not just HOW to implement)
- HOW changes, WHY remains constant

### Validate Before Create
- Always check task validity before creation
- Dependency awareness and resolution
- Circular dependency prevention
- Environment validation before building

### Microservices When Appropriate
- Single responsibility per module
- Independent scaling possible
- HTTP communication between services (no direct imports)
- True separation of concerns

### Trust the Builder
- You provide vision and constraints
- AI handles implementation details
- No hand-holding after approval
- Autonomous execution once started

### Simplicity Default
- Minimal dependencies
- Small modules (< 300 lines)
- Local-first when possible
- No frameworks when tools suffice

### Free Infrastructure
- OCI Always Free Tier
- GitHub Free
- Tailscale Free
- $0/month runtime cost

### Progressive Enhancement
- Build v1 that works
- Iterate to v2 when needed
- Don't over-engineer upfront
- Ship, learn, improve

---

## TROUBLESHOOTING (Archon Systematic Approach)

**Core Debugging Methodology**:
1. **Isolate Layer**: Test each component independently (network → app → database)
2. **Check Dependencies**: Verify required services are running before testing
3. **Analyze Logs**: Always check logs before code changes
4. **Verify Health**: Use `/health` endpoints to verify service status

**If validation fails:**

```bash
# Python missing/wrong version
sudo apt install python3.12 python3.12-venv

# Git not configured
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# GitHub auth failing
gh auth login  # If you have GitHub CLI
# or set up SSH keys

# Tailscale not connected
sudo tailscale up
```

**If build gets stuck:**

```bash
# Check what's running
ps aux | grep python

# Archon: Check service status
systemctl status caddy docker tailscale

# See recent commits
cd ~/[project]
git log --oneline -10

# Check tests
pytest -v

# Check logs (systematic approach)
journalctl -u [service-name] --since "1 hour ago"
tail -100 [project].log

# Port conflicts
lsof -i :PORT

# Docker issues
docker compose logs -f [service-name]
```

**If you need to restart:**
- All code is on GitHub
- All progress committed
- Just continue from where it stopped
- No work is lost

---

## ANTI-PATTERNS TO AVOID (Archon Enhanced)

**Don't:**
- Answer questions vaguely ("make it configurable")
- Skip the validation step
- Change requirements mid-build
- Over-scope v1 (keep it simple)
- Implement services without health endpoints
- Create tight coupling between modules
- Ignore the WHY (focus only on HOW)

**Do:**
- Be specific in answers
- Provide concrete examples
- Start small (can expand later)
- Trust the autonomous process
- Add `/health` endpoints to all services
- Document WHY choices were made
- Follow Validate Before Create principle

---

## ADVANCED PATTERNS (Archon Integration)

### Microservices Communication
```python
# Service A (example)
import requests

def call_service_b(data):
    response = requests.post("http://localhost:8052/api/process", json=data)
    return response.json()
```

### Health Endpoint Pattern
```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}
```

### Caddy Configuration Templates
```caddy
# API service
api.project.ts.net {
    reverse_proxy localhost:8000
    encode gzip
}

# Static site
project.ts.net {
    root * /path/to/files
    file_server
    encode gzip
}

# Mixed (API + Static)
app.project.ts.net {
    handle /api/* {
        reverse_proxy localhost:8000
    }
    handle /* {
        root * /path/to/app
        file_server
        try_files {path} /index.html
    }
    encode gzip
}
```

### Docker Compose Structure
```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Error Handling Pattern
```python
import logging

logger = logging.getLogger(__name__)

def process_data(data):
    try:
        # Main logic
        result = transform(data)
        logger.info(f"Successfully processed {len(data)} items")
        return result
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        # Always log before raising
        raise
```

## NEXT STEPS AFTER FIRST PROJECT

**Once you've built one project with ONE_SHOT:**

1. **Iterate on ONE_SHOT itself**
   - What questions were unclear?
   - What should be asked differently?
   - What defaults could be smarter?

2. **Build your second project**
   - It'll be faster (you know the questions)
   - PRD generation improves
   - Patterns emerge

3. **Create project templates**
   - Save answered questionnaires for project types
   - CLI tool template
   - Web app template
   - Data pipeline template

4. **Contribute improvements**
   - Better questions
   - More project types
   - Smarter defaults

---

## READY?

**Start by answering Q1 above and work through all questions.**

**Once done, say: "Questions complete, run validation"**

**Then we build your project autonomously.**

---

**Version History**
- v1.2 (2024-11-21): Complete Archon integration - systematic debugging, health endpoints, microservices patterns, Caddy templates, Docker best practices
- v1.1 (2024-11-21): Added Archon methodology integration - Validate Before Create, Dependency Awareness, WHY documentation
- v1.0 (2024-11-21): Initial ONE_SHOT framework based on RelayQ, OOS, FrugalOS patterns

---

*This is ONE_SHOT + ARCHON: One file. One workflow. Infinite projects. Systematic excellence.*
