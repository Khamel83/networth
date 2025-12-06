# ONE_SHOT_CONTRACT (do not remove)
```yaml
oneshot:
  version: 3.0

  # ============================================================================
  # ONE_SHOT: THE $0 AI BUILD SYSTEM
  # ============================================================================
  # Single file. Works standalone. Builds anything. Costs nothing.
  #
  # Compatible with: Claude Code, Cursor, Aider, Gemini CLI, any LLM agent
  # Also compatible with: AGENTS.md standard (this file can BE your AGENTS.md)
  # ============================================================================

  # ============================================================================
  # PRIME DIRECTIVE: FRONT-LOAD EVERYTHING
  # ============================================================================
  prime_directive:
    philosophy: |
      ONE_SHOT exists to MINIMIZE user interruptions during development.
      All information gathering happens UPFRONT, before any code is written.
      Once the PRD is approved, the agent works autonomously until done.

      THE FORMULA: 5 min questions → PRD approval → hours of autonomous work → done

    rules:
      - "Ask ALL questions before writing ANY code"
      - "NEVER interrupt the user mid-build for information you could have asked upfront"
      - "If you discover you need new information, BATCH questions together"
      - "Validate answers immediately - don't discover problems 2 hours into coding"
      - "The user's time is precious - your compute time is cheap"

    flow:
      intake: "5-15 min of user time → Complete PRD with no ambiguity"
      autonomous: "Minutes to hours of agent work → User can walk away"
      interruption: "Only for hard_stops (security, data deletion, etc.)"

  # ============================================================================
  # COST: $0 INFRASTRUCTURE + MINIMAL TOKENS
  # ============================================================================
  # ============================================================================
  # INFRASTRUCTURE HIERARCHY
  # ============================================================================
  # Priority order for where to run things. Homelab first, cloud only when needed.
  # ============================================================================
  infrastructure:
    priority_order:
      1_homelab:
        when: "Default - anything that can run locally"
        examples: ["dev servers", "databases", "self-hosted apps", "CI runners"]
        cost: "$0 (electricity only)"
      2_oci_free_tier:
        when: "Needs 24/7 uptime, homelab can't provide"
        examples: ["public APIs", "webhooks", "always-on services"]
        cost: "$0 (forever free tier)"
        specs: "ARM 4 OCPU, 24GB RAM, 200GB storage"
      3_github_actions:
        when: "CI/CD, scheduled tasks, cloud-only operations"
        examples: ["tests", "builds", "deployments", "cron jobs"]
        cost: "$0 (2000 min/month free)"
      4_supabase:
        when: "Need managed Postgres with auth/realtime"
        examples: ["user data", "app state", "auth"]
        cost: "$0 (free tier with keep-alive)"
        note: "Requires keep-alive ping every 7 days to prevent pause"

    supabase_keepalive:
      method: "GitHub Action scheduled workflow"
      schedule: "0 0 */5 * *"  # Every 5 days at midnight
      action: "Simple SELECT 1 query via Supabase REST API"
      workflow_location: "secrets-vault/.github/workflows/supabase-keepalive.yml"

    decision_tree: |
      Q: Does it need 24/7 public access?
        No  → Homelab
        Yes → Q: Is it stateless/simple?
                Yes → OCI Free Tier
                No  → Q: Is it just scheduled tasks?
                        Yes → GitHub Actions
                        No  → Supabase + OCI combo

  cost_optimization:
    infrastructure: "$0 - Homelab → OCI → GitHub Actions → Supabase"
    ai_model:
      default: "google/gemini-2.5-flash-lite"  # ~$0.02/million tokens
      complex: "claude-sonnet-4"               # For architecture decisions
      heavy: "claude-opus-4"                   # For initial setup only
    monthly_target: "$0-5 for most projects"

    token_strategy:
      one_shot_md: "~18K tokens (always loaded)"
      skills_md: "~3K per skill (loaded on-demand)"
      llm_overview: "~2-5K per project"
      total_typical: "~25K tokens per session"

    anti_patterns:
      - "Loading entire codebase into context"
      - "Re-explaining project every session"
      - "Using expensive models for routine tasks"

  # ============================================================================
  # STANDALONE vs SUPPLEMENTED
  # ============================================================================
  # ONE_SHOT works completely standalone. No other files required.
  # But it can be SUPPLEMENTED by external resources for power users.
  # ============================================================================
  standalone:
    works_alone: true
    minimum_files: ["ONE_SHOT.md"]  # This file is all you need
    generates: ["PRD.md", "LLM-OVERVIEW.md", "README.md", ".oneshot/"]

  supplements:
    skills_md:
      url: "https://raw.githubusercontent.com/Khamel83/secrets-vault/master/SKILLS.md"
      local: "~/github/secrets-vault/SKILLS.md"
      when: "For skill-based orchestration (19 reusable skills)"
      required: false
    secrets_vault:
      repo: "github.com/Khamel83/secrets-vault"
      when: "For SOPS+Age encrypted secrets"
      required: false

  # ============================================================================
  # AGENTS.MD COMPATIBILITY
  # ============================================================================
  # ONE_SHOT is compatible with the AGENTS.md standard (2025).
  # You can rename this file to AGENTS.md or symlink it.
  # ============================================================================
  agents_md_compatible: true
  agents_md_note: |
    ONE_SHOT follows the AGENTS.md philosophy:
    - Single file for AI context
    - Project-specific instructions
    - Build/test/deploy guidance

    ONE_SHOT goes BEYOND AGENTS.md:
    - PRD-first development
    - Triage layer for intent classification
    - Checkpoint/resume for long sessions
    - Skills composition for complex builds
    - Cost tracking and optimization

  # ============================================================================
  # THE BUILD LOOP (Aider-inspired)
  # ============================================================================
  # Implement → Test → Fix → Commit → Repeat
  # ============================================================================
  build_loop:
    pattern: |
      for each task in PRD:
        1. implement(task)
        2. test(task)           # Auto-run tests
        3. if test_fails:
             fix(errors)        # Feed errors back to LLM
             goto 2
        4. commit(task)         # Conventional commits
        5. update_checkpoint()

    auto_test:
      enabled: true
      command: "auto-detect from project type"
      on_failure: "Feed error to LLM, attempt fix, max 3 retries"

    auto_lint:
      enabled: true
      command: "auto-detect from project type"
      on_failure: "Auto-fix if possible, otherwise warn"

  # ============================================================================
  # FILE ARCHITECTURE
  # ============================================================================
  architecture:
    current_size: "~18K tokens"
    growth_ceiling: "30-40K tokens"
    priority_order: |
      1. YAML header (always parsed)
      2. Part I Sections 0-7 (core flow)
      3. Part I Sections 8-16 (supporting)
      4. Part II-III (reference)
      5. Part IV (skills index only - full skills external)

  # ============================================================================
  # LLM-OVERVIEW STANDARD
  # ============================================================================
  llm_overview:
    purpose: "Every ONE_SHOT project gets an LLM-OVERVIEW.md file"
    content: "Complete project context for a blank-slate LLM"
    update_frequency: "At milestones, not every commit"
    location: "PROJECT_ROOT/LLM-OVERVIEW.md"

  phases:
    - intake_core_questions   # User present - gather everything
    - generate_prd            # User present - review and approve
    - wait_for_prd_approval   # User says "go"
    - autonomous_build        # User can leave - agent works alone

  modes:
    micro:
      description: "Single file, <100 lines, no project structure needed."
      trigger: "User says 'micro mode' or describes a tiny script"
      required_questions: [Q1, Q6, Q11]
      optional_questions: [Q12]
      skip_sections:
        - web_design
        - ai
        - agents
        - deployment
        - testing
        - health_endpoints
        - scripts_directory
        - llm_overview
      output: "Single script file with inline comments"
    tiny:
      description: "Single script/CLI, no services, no web, no AI."
      skip_sections:
        - web_design
        - ai
        - agents
        - heavy_deployment
    normal:
      description: "CLI or simple web/API on one box. Archon patterns, health checks, basic ops."
      skip_sections: []
    heavy:
      description: "Multi-service and/or AI/agents/MCP with full ops."
      skip_sections: []

  # Tiered questions for speed vs thoroughness
  question_tiers:
    must_answer:
      description: "Always required, no defaults possible"
      questions: [Q0, Q1, Q2, Q6, Q12]
      count: 5
    answer_if_non_default:
      description: "Has smart defaults - only ask if user's needs differ"
      questions: [Q2.5, Q3, Q4, Q5, Q7, Q8, Q9, Q10, Q11, Q13]
      behavior: "Agent proposes defaults, user confirms or overrides"
    yolo_mode:
      trigger: "User says 'yolo mode' or 'fast mode'"
      behavior: "Only ask must_answer questions, use defaults for rest"
      confirmation: "Show proposed defaults, proceed on 'yes'"

  core_questions:
    - { id: Q0,  key: mode,          type: enum,       required: true }
    - { id: Q1,  key: what_build,    type: text,       required: true }
    - { id: Q2,  key: problem,       type: text,       required: true }
    - { id: Q2.5,key: reality_check, type: structured, required: true }
    - { id: Q3,  key: philosophy,    type: text,       required: true }
    - { id: Q4,  key: features,      type: structured, required: true }
    - { id: Q5,  key: non_goals,     type: text,       required: true }
    - { id: Q6,  key: project_type,  type: enum,       required: true }
    - { id: Q7,  key: data_shape,    type: structured, required: true }
    - { id: Q8,  key: data_scale,    type: enum,       required: true }
    - { id: Q9,  key: storage,       type: enum,       required: true }
    - { id: Q10, key: deps,          type: text,       required: false }
    - { id: Q11, key: interface,     type: text,       required: true }
    - { id: Q12, key: done_v1,       type: structured, required: true }
    - { id: Q13, key: naming,        type: structured, required: true }

  variants:
    required_files:
      - ONE_SHOT.md
      - LLM-OVERVIEW.md  # NEW IN v1.8
      - README.md
      - scripts/setup.sh
      - scripts/start.sh
      - scripts/stop.sh
      - scripts/status.sh
    required_web_endpoints:
      - /health
      - /metrics
    storage_upgrade_path:
      - files
      - sqlite
      - postgres
    ai_defaults:
      default_provider: openrouter
      default_model: google/gemini-2.5-flash-lite
      monthly_cost_target_usd: 5

  enforcement:
    presence_rule: >
      If ONE_SHOT.md exists in a repo, agents MUST treat it as the governing
      spec for questions, PRD, implementation order, ops, and AI usage.
    prd_rule: >
      Any non-trivial change (new feature, storage change, deployment change)
      MUST go through PRD update before code changes.
    storage_rule: >
      Agents MUST NOT introduce PostgreSQL unless data_scale is Large (Q8 = C)
      or requirements clearly demand it AND user explicitly approves.
    mode_rule: >
      Agents MUST respect the selected mode's skip_sections when planning
      and implementing work.
    reality_check_rule: >
      If Q2.5 is answered "No, but I might someday" and the project is not
      explicitly marked as a learning project, agents MUST stop after PRD and
      only proceed if the user types the override phrase 'Override Reality Check'.
    llm_overview_rule: >
      Every ONE_SHOT project MUST have an LLM-OVERVIEW.md file that provides
      complete context for a blank-slate LLM to understand the project.
    front_load_rule: >
      Agents MUST gather ALL required information during intake phase.
      NEVER interrupt autonomous build phase for information that could
      have been gathered upfront. User's time is precious; compute is cheap.

  # Hard stops - agent MUST pause and get explicit approval
  hard_stops:
    description: "Agent MUST pause and get explicit user approval before proceeding"
    triggers:
      - id: storage_upgrade
        condition: "Upgrading storage tier (files→SQLite, SQLite→Postgres)"
        prompt: "Storage upgrade requires approval. Current: [X], Proposed: [Y]. Approve?"
      - id: new_major_dependency
        condition: "Adding dependency > 5MB or with native extensions"
        prompt: "Adding [dependency]. This requires [native deps/compilation]. Approve?"
      - id: auth_change
        condition: "Changing authentication method"
        prompt: "Changing auth from [X] to [Y]. This affects [scope]. Approve?"
      - id: production_deploy
        condition: "Any change to production deployment configuration"
        prompt: "Modifying production config. Change: [description]. Approve?"
      - id: reality_check_failed
        condition: "Q2.5 answered 'No, but I might someday' without learning flag"
        prompt: "Reality Check failed. Type 'Override Reality Check' to proceed."
      - id: external_api_integration
        condition: "Adding new external API integration"
        prompt: "Adding [API] integration. Cost: [estimate]. Rate limits: [limits]. Approve?"
      - id: data_deletion
        condition: "Any operation that deletes user data or database tables"
        prompt: "This will delete [description]. Type 'CONFIRM DELETE' to proceed."
      - id: schema_migration
        condition: "Database schema changes on existing data"
        prompt: "Schema migration: [description]. Backup recommended. Approve?"
    agent_behavior: |
      On trigger: STOP → Present prompt → Wait for approval → Log decision → Proceed only after approval
    override:
      pattern: "OVERRIDE: [stop_id]"
      example: "OVERRIDE: storage_upgrade"
      logging: "All overrides MUST be logged to .oneshot/decisions.log"
      format: |
        ## Override: [stop_id]
        **Date**: [ISO timestamp]
        **Reason**: [User's justification]
        **Risk accepted**: [What could go wrong]

  # Agent compatibility notes
  agent_compatibility:
    tested_with:
      - agent: "claude-code"
        model: "claude-opus-4"
        status: "Primary - follows sections literally"
      - agent: "claude-code"
        model: "claude-sonnet-4"
        status: "Good for routine tasks, may need section reminders"
      - agent: "cursor"
        model: "claude-3.5-sonnet"
        status: "May need reminders to check ONE_SHOT.md"
    tips:
      claude_code: "Reference specific sections: 'Follow Section 7.2'"
      cursor: "Start sessions with: 'Read ONE_SHOT.md first'"
    model_selection:
      opus: "Initial setup, complex architecture, multi-phase builds"
      sonnet: "Bug fixes, single features, documentation"
      haiku: "Quick edits, simple scripts"

  # Validation tracking
  validation:
    last_tested: "2024-12-06"
    test_projects:
      - name: "atlas-v2"
        type: "Heavy (AI-powered web app)"
        result: "Pass"
      - name: "divorce-finance"
        type: "Normal (CLI + SQLite)"
        result: "Pass - 135K records"
    primary_agent: "claude-code / claude-opus-4"
    spec_author: "Omar / Khamel83"
    oneshot_version: "2.1"

oneshot_env:
  projects_root: "~/github"
  secrets_vault_repo: "git@github.com:Khamel83/secrets-vault.git"
  secrets_vault_path: "~/github/secrets-vault"
  default_os: "ubuntu-24.04"
  default_user: "ubuntu"

# Companion repository - shared resources for all ONE_SHOT projects
companion_repo:
  name: "secrets-vault"
  repo: "github.com/Khamel83/secrets-vault"
  local_path: "~/github/secrets-vault"
  purpose: "Shared resources, secrets, and detailed reference material"
  contents:
    skills_md:
      file: "SKILLS.md"
      url: "https://raw.githubusercontent.com/Khamel83/secrets-vault/master/SKILLS.md"
      description: "All 9 ONE_SHOT skills with full documentation"
    secrets:
      file: "secrets.env.encrypted"
      description: "SOPS-encrypted secrets for all projects"
    homelab:
      file: "homelab.env"
      description: "Homelab-specific environment config"
  agent_behavior: |
    - Clone/access secrets-vault at project start
    - Fetch SKILLS.md when a skill is triggered
    - Decrypt secrets to .env as needed
    - This repo is the "resource dump" - ONE_SHOT is the "spec"
```
