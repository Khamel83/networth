# ONE_SHOT Claude Skills

This directory contains Claude Code skills that embody the ONE_SHOT philosophy: documentation-first development, security-first practices, and quality-focused automation.

## What Are Skills?

Skills are knowledge packages that teach Claude how to perform tasks better. They use a three-tier loading system:

1. **Metadata** (~100 tokens): Name and description (always loaded)
2. **Instructions** (~5000 tokens): Detailed guidance (loaded when relevant)
3. **Resources** (0 tokens until used): Templates, scripts, examples (on-demand)

This means you can have many skills without bloating context—they only load when needed.

## Available Skills

### Meta Skills

#### 1. skill-creator
**Purpose**: Creates new Claude Code skills following best practices

**Use when**: You need to create a custom skill for a specific workflow

**Invocation**:
- "Create a skill for [task]"
- "Build a new skill"
- "Generate a skill that does [X]"

**What it does**:
- Guides you through skill requirements
- Generates SKILL.md with proper format
- Creates supporting files (templates, examples, validation scripts)
- Follows progressive disclosure architecture

**Example**:
```
"Create a skill for validating Terraform configurations"
```

---

#### 2. marketplace-browser
**Purpose**: Discovers and installs skills from skillsmp.com and community repositories

**Use when**: You want to find existing skills instead of building from scratch

**Invocation**:
- "Find a skill for [task]"
- "Search the marketplace for [domain]"
- "What skills are available for [technology]?"

**What it does**:
- Searches Skills Marketplace (skillsmp.com)
- Browses official Anthropic skills
- Finds community skills from curated repositories
- Provides installation instructions
- Evaluates skill quality and security

**Marketplaces covered**:
- skillsmp.com (primary)
- github.com/anthropics/skills (official)
- Curated awesome lists
- Community repositories (obra, levnikolaevich, mhattingpete, etc.)

---

### Project Management Skills

#### 3. project-initializer
**Purpose**: Bootstraps new projects with ONE_SHOT standards

**Use when**: Starting a new project or converting an existing one to ONE_SHOT standards

**Invocation**:
- "Initialize a new project"
- "Set up project with ONE_SHOT standards"
- "Bootstrap a [type] project"

**What it does**:
- Creates appropriate directory structure (web app, API, CLI, infrastructure)
- Generates CLAUDE.md with project-specific guidance
- Creates comprehensive README.md
- Sets up secrets-vault integration
- Configures quality tools (linting, formatting, testing)
- Initializes git with proper .gitignore
- Creates documentation structure
- Adds CI/CD templates (optional)

**Project types supported**:
- Web applications (React, Next.js, etc.)
- API/Backend services (Express, FastAPI, Go)
- CLI tools
- Infrastructure (Terraform, Kubernetes)

---

#### 4. feature-planner
**Purpose**: Breaks down features into implementable tasks with dependencies

**Use when**: Planning a new feature or complex enhancement

**Invocation**:
- "Plan this feature: [description]"
- "How should we implement [feature]?"
- "Break down this feature"

**What it does**:
- Asks clarifying questions
- Identifies components (frontend, backend, database, testing)
- Creates phased task list
- Maps dependencies between tasks
- Assesses complexity and risks
- Defines testing strategy
- Plans rollout approach

**Output includes**:
- Phased implementation plan
- Task dependencies
- Complexity estimates
- Risk assessment
- Testing strategy
- Success metrics

---

### Development Workflow Skills

#### 5. git-workflow
**Purpose**: Automates git operations with conventional commits and best practices

**Use when**: Committing changes, creating branches, or making PRs

**Invocation**:
- "Commit these changes"
- "Create a PR for this feature"
- "Make a conventional commit"
- "Create a branch for [feature]"

**What it does**:
- Creates conventional commits with proper format
- Follows commit message standards
- Implements branching strategy (feature/, fix/, docs/)
- Generates PR descriptions
- Includes Claude Code attribution
- Checks for secrets before committing

**Commit format**:
```
type(scope): description

[optional body]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**: feat, fix, docs, style, refactor, test, chore, perf, ci

---

#### 6. code-reviewer
**Purpose**: Comprehensive code review including quality, security, and best practices

**Use when**: Reviewing code, PRs, or checking code quality

**Invocation**:
- "Review this code"
- "Check code quality"
- "Review this PR"
- "Security scan this code"

**What it does**:
- **Quality analysis**: Checks for DRY/KISS/YAGNI violations
- **Security scan**: OWASP Top 10 vulnerability checks
- **Best practices**: Code structure, error handling, performance
- **Test coverage**: Verifies adequate testing
- **Documentation**: Checks for proper docs

**Review levels**:
- **Critical**: Security vulnerabilities, breaking changes, data risks
- **Important**: Quality issues, missing tests, error handling gaps
- **Suggestions**: Refactoring opportunities, optimizations

**Output includes**:
- Categorized issues (Critical/Important/Suggestions)
- OWASP Top 10 checklist
- Quality metrics (DRY/KISS/YAGNI)
- Test coverage assessment
- Approve/Request Changes recommendation

---

#### 7. documentation-generator
**Purpose**: Generates comprehensive documentation (READMEs, ADRs, API docs)

**Use when**: Creating or updating documentation

**Invocation**:
- "Generate a README for this project"
- "Create an ADR for [decision]"
- "Generate API documentation"
- "Document this feature"

**What it does**:
- **README.md**: Project overview, installation, usage, examples
- **ADR**: Architecture Decision Records (Nygard format)
- **API docs**: Endpoint specifications with examples
- **CLAUDE.md**: AI assistant guidance
- **User guides**: Step-by-step instructions
- **Developer guides**: Setup and workflows

**Templates included**:
- README.md with badges, examples, troubleshooting
- ADR with context, decision, consequences, alternatives
- API docs with authentication, endpoints, error handling

---

### Security Skills

#### 8. secrets-vault-manager
**Purpose**: Manages secrets using the secrets-vault system

**Use when**: Setting up secrets, accessing API keys, or configuring environment variables

**Invocation**:
- "Set up secrets-vault"
- "I use secrets-vault for environment variables"
- "Configure secrets for this project"

**What it does**:
- Clones secrets-vault (https://github.com/Khamel83/secrets-vault)
- Decrypts secrets using age key
- Sets up .env file (git-ignored)
- Creates .env.example template
- Documents secrets usage
- Integrates with various languages/frameworks

**Setup commands**:
```bash
# Decrypt secrets
age --decrypt -i ~/.age/key.txt ~/secrets-vault/secrets.env.encrypted > .env

# Source variables
source .env

# Verify
printenv | grep API_KEY
```

---

## How Skills Work Together

### Starting a New Project

1. **project-initializer**: Bootstrap project structure
2. **secrets-vault-manager**: Set up secrets management
3. **documentation-generator**: Create initial docs
4. **git-workflow**: Make initial commit

### Planning a Feature

1. **feature-planner**: Break down feature into tasks
2. **documentation-generator**: Create ADR for design decisions
3. **git-workflow**: Create feature branch

### Implementing a Feature

1. **code-reviewer**: Review code as you write
2. **git-workflow**: Commit with conventional messages
3. **documentation-generator**: Update docs

### Creating a PR

1. **code-reviewer**: Final review before PR
2. **git-workflow**: Create PR with proper description
3. **documentation-generator**: Update README if needed

### Discovering New Skills

1. **marketplace-browser**: Search for relevant skills
2. **skill-creator**: Build custom skills for project-specific needs

---

## ONE_SHOT Philosophy

All skills embody these principles:

### 1. Documentation-First
**Before writing code**, check current documentation:
- Local docs: `~/homelab/docs/services/<service-name>/`
- External docs: Use WebFetch/WebSearch for current info
- Verify versions: Check actual versions, don't assume latest
- Use current syntax: Follow current docs, not training data

### 2. Security-First
- Never commit secrets (.env, keys, credentials)
- Use secrets-vault for all projects
- Scan for security vulnerabilities (OWASP Top 10)
- Proper .gitignore configuration

### 3. Quality-Focused
- DRY: Don't repeat yourself
- KISS: Keep it simple
- YAGNI: You aren't gonna need it
- Test early and often
- Code review before merging

### 4. Infrastructure as Code
- Everything version controlled
- Reproducible environments
- Automated deployments
- Configuration validation

---

## Usage Examples

### Example 1: Starting a New API Project

```
User: "Initialize a new FastAPI project"

Claude: [Uses project-initializer]
- Creates API directory structure
- Sets up FastAPI dependencies
- Generates CLAUDE.md with FastAPI conventions
- Creates README with API examples
- Sets up pytest for testing
- Configures black/pylint for code quality
- Initializes git with proper .gitignore

User: "Set up secrets"

Claude: [Uses secrets-vault-manager]
- Decrypts secrets to .env
- Adds .env to .gitignore
- Creates .env.example
- Documents secrets usage in README
```

### Example 2: Planning and Implementing a Feature

```
User: "Plan a feature for user authentication with JWT"

Claude: [Uses feature-planner]
- Asks clarifying questions (OAuth, email/password, etc.)
- Breaks down into phases:
  * Database schema (users table)
  * JWT token generation/validation
  * Login/register endpoints
  * Middleware for protected routes
  * Tests for each component
- Identifies risks and dependencies

User: "Create a branch and start implementing"

Claude: [Uses git-workflow]
- Creates feature/user-auth branch
- Makes initial commit with plan

User: "Review the authentication code"

Claude: [Uses code-reviewer]
- Checks for security issues (password hashing, JWT secret security)
- Validates error handling
- Ensures tests cover edge cases
- Verifies OWASP compliance
```

### Example 3: Finding and Using Community Skills

```
User: "Find a skill for testing with Playwright"

Claude: [Uses marketplace-browser]
- Searches skillsmp.com
- Finds official Anthropic webapp-testing skill
- Provides installation instructions
- Shows usage examples

User: "Install it"

Claude:
- Downloads webapp-testing skill
- Places in .claude/skills/
- Verifies installation
- Shows how to invoke it
```

---

## Creating Custom Skills

### When to Create a Custom Skill

Create a custom skill when you:
- Perform a task repeatedly (3+ times)
- Have domain-specific knowledge to capture
- Need consistent workflow enforcement
- Want to share knowledge with team

### How to Create a Custom Skill

```
User: "Create a skill for validating Docker Compose files against current docs"

Claude: [Uses skill-creator]
1. Asks clarifying questions:
   - What validation rules?
   - Which Docker Compose version?
   - Should it auto-fix issues?

2. Creates skill structure:
   .claude/skills/docker-compose-validator/
   ├── SKILL.md
   ├── scripts/validate.py
   ├── examples/valid-compose.yml
   └── resources/compose-spec.md

3. Generates comprehensive SKILL.md:
   - When to use (keywords, triggers)
   - Validation workflow
   - Error detection and fixes
   - Current syntax references

4. Creates Python validator script

5. Tests the skill with example files
```

---

## Skill File Structure

Each skill follows this structure:

```
.claude/skills/
└── skill-name/
    ├── SKILL.md              # Required: Main skill file
    ├── templates/            # Optional: Reusable templates
    │   ├── template1.md
    │   └── template2.json
    ├── examples/             # Optional: Example inputs/outputs
    │   ├── example1.txt
    │   └── example2.yml
    ├── scripts/              # Optional: Validation/automation scripts
    │   ├── validate.py
    │   └── process.sh
    └── resources/            # Optional: Reference documentation
        └── reference.md
```

### SKILL.md Format

```yaml
---
name: skill-name                      # Required: lowercase, hyphens, max 64 chars
description: Brief description        # Required: max 1024 chars
version: "1.0.0"                     # Optional: semantic versioning
allowed-tools: [Bash, Read, Write]   # Optional: restrict tool access
model: claude-sonnet-4-5             # Optional: request specific model
---

# Skill Title

Description of what this skill does.

## When to Use This Skill

- Trigger condition 1
- Trigger condition 2
- Keywords: keyword1, keyword2

## Instructions

[Detailed instructions in markdown]

## Examples

[Concrete examples with inputs and outputs]

## Resources

- [Link to template](./templates/template.md)
- [Link to example](./examples/example.txt)
```

---

## Best Practices

### Skill Design

1. **Clear Invocation Triggers**: Make keywords/descriptions specific
2. **Progressive Disclosure**: Use templates/resources for large content
3. **Least Privilege**: Restrict tools with `allowed-tools` when possible
4. **Include Examples**: Show 2-3 concrete examples
5. **Ask Questions**: Help Claude gather requirements
6. **Validation Scripts**: Ensure consistency for structured output

### Skill Organization

```
.claude/skills/
├── README.md                    # This file
├── meta/                        # Meta skills
│   ├── skill-creator/
│   └── marketplace-browser/
├── project/                     # Project management
│   ├── project-initializer/
│   └── feature-planner/
├── development/                 # Development workflow
│   ├── git-workflow/
│   ├── code-reviewer/
│   └── documentation-generator/
└── security/                    # Security
    └── secrets-vault-manager/
```

### Maintenance

- **Review quarterly**: Remove unused skills, update outdated ones
- **Test after updates**: Verify skills work after Claude Code updates
- **Document changes**: Keep version numbers updated
- **Share learnings**: Contribute useful skills back to community

---

## Troubleshooting

### Skill Not Being Invoked

**Problem**: Claude doesn't use the skill when expected

**Solutions**:
1. Check skill description includes relevant keywords
2. Be more explicit: "Use the [skill-name] skill"
3. Verify SKILL.md has proper YAML frontmatter
4. Restart Claude Code after creating/modifying skills

### Skill Loading Slowly

**Problem**: Skill takes long to load

**Solutions**:
1. Move large content to templates/ or resources/
2. Use progressive disclosure (don't inline everything)
3. Check skill isn't loading unnecessary data

### Multiple Skills Conflicting

**Problem**: Multiple skills trigger for same task

**Solutions**:
1. Make skill descriptions more specific
2. Use `disable-model-invocation: true` for manual-only skills
3. Consolidate overlapping skills

---

## Resources

### Official Documentation
- [Claude Code Skills Guide](https://docs.claude.com/en/docs/claude-code/skills)
- [Skills Specification](https://github.com/anthropics/skills/blob/main/agent_skills_spec.md)

### Marketplaces
- [Skills Marketplace](https://skillsmp.com)
- [Anthropic Official Skills](https://github.com/anthropics/skills)

### Community
- [Awesome Claude Skills](https://github.com/travisvn/awesome-claude-skills)
- [VoltAgent Awesome Skills](https://github.com/VoltAgent/awesome-claude-skills)

### ONE_SHOT
- [ONE_SHOT Repository](https://github.com/khamel83/oneshot)
- [Secrets Vault](https://github.com/Khamel83/secrets-vault)

---

## Contributing

To add a skill to this collection:

1. Use the `skill-creator` skill to generate proper structure
2. Follow naming conventions (lowercase, hyphens)
3. Include comprehensive examples
4. Test the skill thoroughly
5. Document in this README
6. Commit with: `feat(skills): add [skill-name] skill`

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

**Last Updated**: 2025-12-02
**Skills Version**: 1.0.0
**Total Skills**: 8 (2 meta, 2 project, 3 development, 1 security)
