# ONE_SHOT Orchestrator v6.0

> **IMPORTANT**: This file controls skill and agent routing. Parse the routers first.

---

## SKILL ROUTER (Parse First)

**When user says → Trigger this skill:**

```yaml
skill_router:
  # CORE - Always check these first
  - pattern: "new project|build me|start fresh|create.*app|make.*tool|help me|/interview|/front-door"
    skill: front-door
    chain: [create-plan, implement-plan]

  - pattern: "stuck|looping|confused|not working|start over|broken build"
    skill: failure-recovery

  - pattern: "think|consider|analyze|ultrathink|super think|mega think"
    skill: thinking-modes

  # PLANNING - Before building
  - pattern: "plan|design|architect|how should|what's the approach"
    skill: create-plan
    next: implement-plan

  - pattern: "implement|execute|build it|do it|run the plan"
    skill: implement-plan
    requires: approved_plan

  - pattern: "api|endpoints|routes|rest|graphql"
    skill: api-designer

  # CONTEXT - Session management
  - pattern: "handoff|save context|preserve|before clear|context low"
    skill: create-handoff

  - pattern: "resume|continue|pick up|where.*left|from handoff"
    skill: resume-handoff

  # PERSISTENT TASKS - Cross-session memory
  - pattern: "beads|ready tasks|what's next|dependencies|blockers|persistent tasks"
    skill: beads

  # DEVELOPMENT - During building
  - pattern: "bug|error|fix|debug|not working|fails"
    skill: debugger

  - pattern: "test|verify|check|run tests|make sure"
    skill: test-runner

  - pattern: "review|code quality|check.*code|pr review"
    skill: code-reviewer

  - pattern: "refactor|clean up|improve|restructure"
    skill: refactorer

  - pattern: "slow|performance|optimize|speed|faster"
    skill: performance-optimizer

  # OPERATIONS - Deploy & maintain
  - pattern: "commit|push|branch|merge|pr|pull request"
    skill: git-workflow

  - pattern: "deploy|ship|cloud|host|production|oci"
    skill: push-to-cloud

  - pattern: "run on|execute on|ssh to|sync and run|process on macmini|homelab docker|remote|tmux job"
    skill: remote-exec

  - pattern: "ci|cd|github actions|pipeline|automation"
    skill: ci-cd-setup

  - pattern: "docker|container|compose|kubernetes"
    skill: docker-composer

  - pattern: "monitoring|observability|metrics|logging|alerts|health check"
    skill: observability-setup

  # DATA & DOCS
  - pattern: "database|schema|migration|postgres|sqlite"
    skill: database-migrator

  - pattern: "oci database|oracle|autonomous|object storage|bucket|khameldb"
    skill: oci-resources

  - pattern: "convex|reactive database|real-time backend|convex setup"
    skill: convex-resources

  - pattern: "docs|readme|documentation|explain"
    skill: documentation-generator

  - pattern: "sync secrets|pull secrets|push secrets|secrets diff|compare secrets"
    skill: secrets-sync

  - pattern: "secrets|env|credentials|api key|encrypt"
    skill: secrets-vault-manager

  # AGENT DELEGATION - For isolated context work
  - pattern: "delegate|spawn agent|isolated|background task"
    skill: delegate-to-agent

  # COMMUNICATION - Strategic filtering
  - pattern: "audit this|filter this|make this strategic|before I send|high-stakes|check this message"
    skill: the-audit
```

---

## DIAGNOSTIC MODE

When user says "which skill?" or "what skill would you use for X?":
1. Identify the skill that would be triggered
2. Show the matching trigger pattern
3. Do NOT execute the skill

Example:
> User: "which skill would you use for: fix this bug"
> Assistant: "That would trigger **debugger** (pattern: `bug|error|fix|debug`)"

---

## AGENT ROUTER (Native Sub-agents)

**When to use agents instead of skills:**
- Task would read 10+ files (context pollution)
- Security audit requiring isolation
- Long-running operations (tests, builds)
- Parallel exploration of multiple areas

```yaml
agent_router:
  # Security - isolated review
  - pattern: "security audit|OWASP|vulnerabilities|pentest|secrets scan"
    agent: security-auditor
    model: sonnet
    tools: [Read, Grep, Glob, Bash]
    reason: "Isolated context for thorough security analysis"

  # Research - deep codebase exploration
  - pattern: "explore|find all|how does.*work|trace|understand|deep dive"
    agent: deep-research
    model: haiku
    tools: [Read, Grep, Glob, WebFetch, WebSearch]
    reason: "Long research without polluting main context"

  # Background - long-running tasks
  - pattern: "background|parallel|run tests|build|long task"
    agent: background-worker
    model: haiku
    tools: [Bash, Read, Write]
    permissionMode: acceptEdits
    reason: "Non-blocking execution of long tasks"

  # Coordination - multi-agent orchestration
  - pattern: "coordinate|multiple agents|parallel exploration|divide and conquer"
    agent: multi-agent-coordinator
    model: sonnet
    tools: [Read, Grep, Glob, Bash]
    reason: "Orchestrate multiple agents for complex tasks"
```

---

## SKILLS vs AGENTS

| Aspect | Skills | Agents |
|--------|--------|--------|
| **Context** | Shared with main conversation | Isolated window |
| **Best for** | Quick, synchronous tasks | Long research, background work |
| **Model** | Inherits from session | Configurable per agent |
| **Invocation** | Automatic via router | Via Task tool or explicit |
| **Resumable** | Via handoff files | Via agentId |

**Decision guide:**
- Quick code review → `code-reviewer` skill
- Deep security audit → `security-auditor` agent
- Simple debug → `debugger` skill
- Multi-file exploration → `deep-research` agent

---

## AVAILABLE AGENTS (4)

| Agent | Model | Purpose |
|-------|-------|---------|
| `security-auditor` | sonnet | Isolated OWASP/secrets/auth review |
| `deep-research` | haiku | Long codebase exploration |
| `background-worker` | haiku | Parallel test/build execution |
| `multi-agent-coordinator` | sonnet | Multi-agent orchestration |

---

## AVAILABLE SKILLS (28)

| Category | Skills | Purpose |
|----------|--------|---------|
| **Core** | `front-door`, `failure-recovery`, `thinking-modes` | Orchestration, recovery, cognition |
| **Planning** | `create-plan`, `implement-plan`, `api-designer` | Design before building |
| **Context** | `create-handoff`, `resume-handoff`, `beads` | Session persistence, cross-session memory |
| **Development** | `debugger`, `test-runner`, `code-reviewer`, `refactorer`, `performance-optimizer` | Build & quality |
| **Operations** | `git-workflow`, `push-to-cloud`, `remote-exec`, `ci-cd-setup`, `docker-composer`, `observability-setup` | Deploy & maintain |
| **Data & Docs** | `database-migrator`, `documentation-generator`, `secrets-vault-manager`, `secrets-sync`, `oci-resources`, `convex-resources` | Support |
| **Communication** | `the-audit` | Strategic communication filter |
| **Agent Bridge** | `delegate-to-agent` | Route to native sub-agents |

---

## THINKING MODES

| Level | Trigger | Use |
|-------|---------|-----|
| **Think** | "think" | Quick check |
| **Think Hard** | "think hard" | Trade-offs |
| **Ultrathink** | "ultrathink" | Architecture |
| **Super Think** | "super think" | System design |
| **Mega Think** | "mega think" | Strategic |

> **Pro tip**: "ultrathink please do a good job"

---

## SKILL CHAINS

Common workflows that compose multiple skills:

```yaml
chains:
  new_project:
    1: front-door        # Interview → Spec
    2: create-plan       # Structure approach
    3: implement-plan    # Build it

  add_feature:
    1: create-plan       # Plan the feature
    2: implement-plan    # Build it
    3: test-runner       # Verify

  debug_issue:
    1: thinking-modes    # Analyze (ultrathink)
    2: debugger          # Systematic fix
    3: test-runner       # Verify fix

  deploy:
    1: code-reviewer     # Pre-deploy check
    2: push-to-cloud     # Deploy
    3: ci-cd-setup       # Automate future

  session_break:
    1: create-handoff    # Save state
    # /clear
    2: resume-handoff    # Continue
```

---

## PHILOSOPHY: The Spolsky Doctrine

> "It's harder to read code than to write it." — Joel Spolsky

**NEVER rewrite from scratch.** This is the single worst strategic decision in software.

### Why Old Code Isn't Bad

Every line of "ugly" code contains:
- Bug fixes discovered through real-world use
- Edge cases that took weeks to reproduce
- Hard-won knowledge about compatibility and performance

When programmers say code is messy, they're usually wrong. They mistake *unfamiliarity* for *poor quality*.

### The AI Advantage

Unlike humans, AI has no bias toward writing over reading:
- **Reading unfamiliar code is cheap** for AI — no ego, no fatigue
- **Understanding existing solutions** takes seconds, not hours
- **Extending battle-tested code** beats starting fresh every time

### The GitHub Corollary

**If someone already solved this problem, USE THEIR SOLUTION.**

Before writing new code, ask:
1. Is there a popular library that does this?
2. Is there an open-source project solving this exact problem?
3. Can we extend/fork existing work instead of starting from zero?

Popular projects on GitHub represent thousands of hours of debugging, edge-case handling, and real-world testing. That knowledge is free. Use it.

### Refactor, Don't Rewrite

When improving code:
- **1% of work gets 99% of results** — target bottlenecks, not wholesale replacement
- **Incremental improvement** beats big-bang rewrites
- **Preserve institutional knowledge** encoded in existing code

---

## YAML CONFIG

```yaml
oneshot:
  version: 6.0
  skills: 28
  agents: 4

  prime_directive: |
    USER TIME IS PRECIOUS. AGENT COMPUTE IS CHEAP.
    Ask ALL questions UPFRONT. Get ALL info BEFORE coding.
    NEVER REWRITE FROM SCRATCH. Extend, refactor, use existing solutions.

  file_hierarchy:
    1: CLAUDE.md        # Project-specific (read first)
    2: AGENTS.md        # This file (skill routing)
    3: TODO.md          # Progress tracking
    4: LLM-OVERVIEW.md  # Project context

  build_loop: |
    for each task:
      1. Mark "In Progress" in TODO.md
      2. Use appropriate skill
      3. Test
      4. Commit
      5. Mark "Done ✓" in TODO.md

  hard_stops:
    - "Storage upgrade (files→SQLite→Postgres)"
    - "Auth method changes"
    - "Production deployment"
    action: "STOP → Ask user → Wait for approval"

  logging:
    enabled: true
    file: SKILL_LOG.md
    format: "| {date} | {skill} | {trigger} | {result} |"
    note: "Append entry after each skill invocation"
```

---

## PLAN WORKFLOW

```
/create_plan [idea]      → thoughts/shared/plans/YYYY-MM-DD-description.md
  └─ answer questions, get approval

/implement_plan @[plan]  → systematic execution
  └─ context low?

/create_handoff          → thoughts/shared/handoffs/YYYY-MM-DD-handoff.md
  └─ /clear

/resume_handoff @[file]  → continue exactly where left off
```

---

## CORE QUESTIONS (Ask Upfront)

| ID | Question | Required |
|----|----------|----------|
| Q0 | Mode (micro/tiny/normal/heavy) | Yes |
| Q1 | What are you building? | Yes |
| Q2 | What problem does this solve? | Yes |
| Q4 | Features (3-7 items) | Yes |
| Q6 | Project type (CLI/Web/API) | Yes |
| Q12 | Done criteria / v1 scope | Yes |

---

## TRIAGE (First 30 Seconds)

| Intent | Signals | Skill |
|--------|---------|-------|
| build_new | "new project", "build me" | front-door |
| fix_existing | "broken", "bug", "error" | debugger |
| continue_work | "resume", "checkpoint" | resume-handoff |
| add_feature | "add feature", "extend" | create-plan |
| deploy | "deploy", "push" | push-to-cloud |
| stuck | "looping", "confused" | failure-recovery |
| refine_communication | "audit this", "filter this", "before I send" | the-audit |

---

## ALWAYS UPDATE

| File | When |
|------|------|
| **TODO.md** | Every task state change |
| **LLM-OVERVIEW.md** | Major architectural changes |

---

## RESET

Say `(ONE_SHOT)` to re-anchor to these rules.

---

**Version**: 6.0 | **Skills**: 28 | **Agents**: 4 | **Cost**: $0

Compatible: Claude Code, Cursor, Aider, Gemini CLI
