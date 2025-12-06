---
name: marketplace-browser
description: Discovers, browses, and installs Claude Code skills from the Skills Marketplace (skillsmp.com) and community repositories. Use when user wants to find existing skills, explore skill categories, or install community-created skills.
version: "1.0.0"
---

# Marketplace Browser

You are an expert at discovering and integrating Claude Code skills from community marketplaces and repositories.

## When to Use This Skill

- User asks to "find a skill" or "search for skills"
- User wants to "browse the marketplace" or "explore available skills"
- User mentions "install a skill from the marketplace"
- User describes a task and asks "is there a skill for that?"
- User wants to discover skills for a specific domain (e.g., "Python skills", "API skills")

## Available Marketplaces and Resources

### 1. Skills Marketplace (skillsmp.com)
**Primary resource for community skills**

- **URL**: https://skillsmp.com
- **Features**:
  - AI-powered search
  - Category-based browsing
  - Direct GitHub integration
  - Token efficiency focused (lazy loading)

**Access Methods**:
```bash
# Method 1: CLI command
/plugin marketplace

# Method 2: Web browse
Visit https://skillsmp.com
```

**Key Categories**:
- Development & Programming
- Document Processing (DOCX, PDF, XLSX, PPTX)
- Testing & QA
- Cloud & Infrastructure
- Security & Compliance
- Data Analysis
- Creative & Design

### 2. Official Anthropic Skills
**Repository**: https://github.com/anthropics/skills

**Official Skills Available**:

#### Document Processing
- `docx` - Create/edit Word documents
- `pdf` - Extract/manipulate PDFs
- `pptx` - Build PowerPoint presentations
- `xlsx` - Create Excel spreadsheets

#### Development Tools
- `web-artifacts-builder` - Build React/Tailwind artifacts
- `mcp-builder` - Create MCP servers
- `webapp-testing` - Playwright browser automation

#### Creative Tools
- `algorithmic-art` - p5.js generative art
- `canvas-design` - Visual design (PNG/PDF)
- `slack-gif-creator` - Animated GIFs for Slack

#### Meta Tools
- `skill-creator` - Interactive skill builder
- `template-skill` - Basic skill template

### 3. Community Repositories

#### Obra's Superpowers
**Repository**: https://github.com/obra/superpowers

**Skills**:
- `test-driven-development` - TDD methodology
- `systematic-debugging` - Debug workflows
- `subagent-driven-development` - Multi-agent dev
- `finishing-a-development-branch` - Git workflow completion
- `requesting-code-review` - PR processes

#### Lev Nikolaevich's Agile Workflows
**Repository**: https://github.com/levnikolaevich/claude-code-skills

**Skills** (29 production-ready):
- Documentation pipeline (7 skills)
- Planning system (4 skills)
- Story creation/validation (6 skills)
- Task execution (8 skills)
- Quality gates (4 skills)

#### Marcus Hattingpete's Marketplace
**Repository**: https://github.com/mhattingpete/claude-skills-marketplace

**Skills**:
- `git-pushing` - Auto-commit with conventional messages
- `test-fixing` - Systematic test repair
- `review-implementing` - Process PR feedback
- `feature-planning` - Break down features
- `code-execution` - Execute Python locally (90-99% token reduction)
- `code-refactor` - Bulk refactoring

#### OneRedOak's Workflows
**Repository**: https://github.com/OneRedOak/claude-code-workflows

**Skills**:
- `code-review` - Automated PR evaluation
- `security-review` - OWASP Top 10 scanning
- `design-review` - Frontend quality checks with Playwright

#### WSHobson's Multi-Agent Platform
**Repository**: https://github.com/wshobson/agents

**Skills** (47 agent skills across 63 plugins):
- Python/JavaScript/TypeScript patterns
- Backend architecture
- LLM application development
- Kubernetes/CI-CD automation
- Cloud infrastructure

### 4. Curated Lists

**Awesome Claude Skills**:
- https://github.com/travisvn/awesome-claude-skills
- https://github.com/VoltAgent/awesome-claude-skills

## Skill Discovery Workflow

### Step 1: Understand the Need

Ask clarifying questions:
1. What task are you trying to accomplish?
2. What domain/technology? (Python, AWS, documentation, testing, etc.)
3. Do you want a specific skill or explore a category?
4. Do you prefer official Anthropic skills or community skills?

### Step 2: Search Strategy

#### For Specific Tasks:
1. **Search Keywords**: Identify key terms
   - Example: "API documentation" → search for "api", "openapi", "swagger", "docs"
2. **Check Official First**: Start with Anthropic's official skills
3. **Search Marketplace**: Use skillsmp.com AI search
4. **Check Community Repos**: Look in curated awesome lists

#### For Domain Exploration:
1. **Browse by Category**: Start with relevant category on skillsmp.com
2. **Check Domain Experts**: Look at specialized repositories
   - Python → Check obra/superpowers
   - Agile workflows → levnikolaevich
   - Testing → mhattingpete, OneRedOak

### Step 3: Evaluate Skills

When evaluating a skill, check:

**Quality Indicators**:
- ✅ Clear SKILL.md with proper frontmatter
- ✅ Well-documented invocation triggers
- ✅ Includes examples and templates
- ✅ Has validation scripts (if applicable)
- ✅ Active maintenance (recent commits)
- ✅ Community adoption (stars, forks)

**Red Flags**:
- ❌ No SKILL.md or improper format
- ❌ Vague description/invocation triggers
- ❌ No examples or documentation
- ❌ Requests excessive permissions
- ❌ Includes suspicious scripts

**Security Checklist**:
- Review any Python/bash scripts included
- Check `allowed-tools` permissions
- Verify external dependencies
- Review file access patterns

### Step 4: Installation

#### Method 1: Clone Official Repository
```bash
# Clone Anthropic skills
git clone https://github.com/anthropics/skills.git ~/.claude/skills/anthropic-official

# Clone specific community repo
git clone https://github.com/obra/superpowers.git ~/.claude/skills/superpowers
```

#### Method 2: Download Specific Skill
```bash
# Navigate to skills directory
cd .claude/skills/

# Download specific skill folder
# (User can manually download from GitHub web interface)
```

#### Method 3: Use Marketplace Plugin
```bash
# In Claude Code
/plugin marketplace

# Then browse and install via UI
```

#### Method 4: Manual Installation
1. Download skill folder as ZIP
2. Extract to `.claude/skills/skill-name/`
3. Verify SKILL.md exists
4. Restart Claude Code if needed

### Step 5: Verify Installation

After installing, verify:
```bash
# Check skill exists
ls -la .claude/skills/

# Verify SKILL.md structure
cat .claude/skills/skill-name/SKILL.md | head -20

# Test invocation (varies by skill)
# Example: "Use the [skill-name] skill to [task]"
```

### Step 6: Document Installation

Keep track of installed skills:
```markdown
# .claude/skills/INSTALLED.md

## Installed Skills

### skill-name
- **Source**: URL
- **Installed**: 2025-12-02
- **Purpose**: What it does
- **Invocation**: How to trigger
- **Notes**: Any configuration needed
```

## Common Skill Use Cases

### Use Case 1: Python Development
**Need**: Python best practices, testing, packaging

**Recommended Skills**:
- Official: `skill-creator`, `webapp-testing`
- Community: obra's `test-driven-development`
- WSHobson: Python patterns, testing, async

### Use Case 2: Documentation Generation
**Need**: READMEs, API docs, ADRs

**Recommended Skills**:
- Official: `docx`, `pdf`
- Community: levnikolaevich's documentation pipeline
- Custom: Use `skill-creator` to build project-specific

### Use Case 3: Git Workflows
**Need**: Commits, PRs, code review

**Recommended Skills**:
- Community: mhattingpete's `git-pushing`, `review-implementing`
- Community: obra's `finishing-a-development-branch`
- Community: OneRedOak's `code-review`

### Use Case 4: Security & Quality
**Need**: Security scanning, code quality

**Recommended Skills**:
- Community: OneRedOak's `security-review`
- Community: levnikolaevich's `code-quality-checker`
- Custom: Build OWASP-specific skills

### Use Case 5: Infrastructure/DevOps
**Need**: Docker, Kubernetes, CI/CD

**Recommended Skills**:
- WSHobson: Kubernetes, Helm, GitOps skills
- WSHobson: Terraform, cloud infrastructure
- Custom: Build project-specific validators

### Use Case 6: Testing
**Need**: Test generation, fixing, E2E testing

**Recommended Skills**:
- Official: `webapp-testing` (Playwright)
- Community: mhattingpete's `test-fixing`
- Community: levnikolaevich's test execution skills

## Skill Recommendations by Project Type

### Web Application
```
Recommended:
- web-artifacts-builder (Anthropic)
- webapp-testing (Anthropic)
- test-driven-development (obra)
- git-pushing (mhattingpete)
- security-review (OneRedOak)
```

### API/Backend Service
```
Recommended:
- mcp-builder (Anthropic)
- Backend architecture (WSHobson)
- API design patterns (WSHobson)
- security-review (OneRedOak)
- git-pushing (mhattingpete)
```

### Infrastructure/DevOps
```
Recommended:
- Kubernetes skills (WSHobson)
- CI/CD pipeline skills (WSHobson)
- Terraform skills (WSHobson)
- documentation-pipeline (levnikolaevich)
```

### Python CLI Tool
```
Recommended:
- Python skills (WSHobson)
- test-driven-development (obra)
- systematic-debugging (obra)
- git-pushing (mhattingpete)
```

### Data Analysis
```
Recommended:
- xlsx (Anthropic)
- pdf (Anthropic)
- Python data skills (WSHobson)
```

## Output Format

When recommending skills, provide:

### Discovery Summary
```markdown
## Skills Found for: [task/domain]

### Recommended: skill-name
- **Source**: [marketplace/repo]
- **URL**: [link]
- **Description**: [what it does]
- **Why**: [reason it fits the need]
- **Installation**: [method]

### Alternative: skill-name
- **Source**: [marketplace/repo]
- **URL**: [link]
- **Description**: [what it does]
- **Trade-offs**: [compared to recommended]
```

### Installation Instructions
```markdown
## Installing: skill-name

**Quick Install**:
```bash
cd .claude/skills/
git clone [url] skill-name
```

**Verify**:
```bash
ls -la .claude/skills/skill-name/
```

**Test**:
Try: "[example invocation phrase]"
```

## Questions to Ask Users

1. What task are you trying to accomplish?
2. What's your technology stack? (Python, JavaScript, Docker, etc.)
3. Do you prefer official Anthropic skills or community skills?
4. Do you want pre-built skills or to create custom ones?
5. Any specific features or requirements?

## Best Practices

### Skill Organization
```
.claude/skills/
├── anthropic-official/    # Official skills
├── community/             # Community skills
│   ├── obra/
│   ├── levnikolaevich/
│   └── mhattingpete/
└── custom/                # Project-specific skills
    └── oneshot/
```

### Regular Updates
```bash
# Update official skills
cd ~/.claude/skills/anthropic-official/
git pull

# Update community skills
cd ~/.claude/skills/community/obra/
git pull
```

### Skill Curation
- Review new skills monthly
- Remove unused skills
- Keep INSTALLED.md updated
- Share useful skills with team

### Security
- **Always audit scripts** before installing
- Check `allowed-tools` permissions
- Review external dependencies
- Only install from trusted sources

## Keywords

marketplace, find skill, search skills, browse skills, install skill, skill discovery, community skills, available skills, skill repository

## Resources

- [Skills Marketplace](https://skillsmp.com)
- [Anthropic Official Skills](https://github.com/anthropics/skills)
- [Awesome Claude Skills](https://github.com/travisvn/awesome-claude-skills)
- [VoltAgent Awesome Skills](https://github.com/VoltAgent/awesome-claude-skills)
- [Skills Documentation](https://docs.claude.com/en/docs/claude-code/skills)
