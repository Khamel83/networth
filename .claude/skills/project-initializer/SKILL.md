---
name: project-initializer
description: Bootstraps new projects with ONE_SHOT standards - documentation-first approach, secrets-vault integration, git setup, quality tooling, and best practices. Use when starting a new project or converting existing project to ONE_SHOT standards.
version: "1.0.0"
allowed-tools: [Bash, Read, Write, Grep, Glob]
---

# Project Initializer

You are an expert at bootstrapping projects following ONE_SHOT's philosophy: documentation-first, security-first, quality-focused development.

## When to Use This Skill

- User says "initialize new project" or "start new project"
- User asks to "set up project with ONE_SHOT standards"
- User mentions "bootstrap project" or "create project structure"
- User wants to "convert project to ONE_SHOT standards"
- Starting any new development effort

## ONE_SHOT Philosophy

### Core Principles

1. **Documentation-First**: Always check current documentation before writing code
2. **Version-Specific**: Verify actual versions, don't assume latest
3. **Security-First**: Secrets management, .gitignore, security scanning
4. **Quality-Focused**: Linting, testing, code quality from day one
5. **Infrastructure as Code**: Everything version controlled and reproducible

### Documentation-First Mandate

**CRITICAL**: Before writing any code that uses external APIs, libraries, or configuration syntax:
1. Check local cached docs first: `~/homelab/docs/services/<service-name>/`
2. If local docs don't exist, use WebFetch/WebSearch for current documentation
3. Verify version compatibility (actual version running, not assumed)
4. Write code using current syntax from verified docs

## Project Initialization Workflow

### Step 1: Gather Project Information

Ask the user:

1. **Project name**: What's the project called?
2. **Project type**: Web app, API, CLI tool, library, infrastructure, etc.?
3. **Technology stack**: Languages, frameworks, databases?
4. **Purpose**: One-sentence description of what this project does
5. **Scope**: Personal, team, open-source?
6. **Requirements**: Any specific tools, patterns, or constraints?

### Step 2: Create Directory Structure

Based on project type, create appropriate structure:

#### Web Application
```
project-name/
├── .claude/
│   ├── CLAUDE.md
│   └── skills/
├── src/
│   ├── components/
│   ├── pages/
│   └── utils/
├── tests/
├── docs/
├── .gitignore
├── README.md
└── package.json (or requirements.txt, go.mod, etc.)
```

#### API/Backend Service
```
project-name/
├── .claude/
│   └── CLAUDE.md
├── cmd/ (or src/)
├── internal/
├── api/
├── tests/
├── docs/
│   └── api/
├── .gitignore
├── README.md
└── docker-compose.yml
```

#### CLI Tool
```
project-name/
├── .claude/
│   └── CLAUDE.md
├── cmd/
├── internal/
├── tests/
├── docs/
├── .gitignore
├── README.md
└── Makefile
```

#### Infrastructure/DevOps
```
project-name/
├── .claude/
│   └── CLAUDE.md
├── terraform/ (or ansible/, k8s/)
├── scripts/
├── docs/
│   └── architecture/
├── .gitignore
├── README.md
└── docker-compose.yml
```

### Step 3: Initialize Git Repository

```bash
# Initialize git
git init

# Create initial .gitignore
cat > .gitignore << 'EOF'
# Secrets
.env*
!.env.example
secrets.env
secrets.*.env
*.key
*_key
key.txt

# Dependencies
node_modules/
vendor/
__pycache__/
*.pyc
.venv/
venv/

# Build outputs
dist/
build/
*.o
*.a
*.so
*.exe

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db
EOF

# Create .claude directory
mkdir -p .claude/skills

# Initial commit
git add .gitignore .claude/
git commit -m "chore: initialize project structure

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 4: Create CLAUDE.md

Generate project-specific CLAUDE.md file:

```markdown
# CLAUDE.md - Project Configuration

This file provides guidance to Claude Code for working on this project.

## Project Overview

**Name**: [Project Name]
**Type**: [Web App/API/CLI/Infrastructure]
**Tech Stack**: [Languages, frameworks, tools]

**Purpose**: [One-sentence description]

## Documentation-First Rule

**Before writing any code**, check documentation:

1. **Check local docs**: If this project has a `docs/` directory, read relevant docs first
2. **Check external docs**: For external libraries/APIs, fetch current documentation
3. **Verify versions**: Check actual versions before assuming syntax
4. **Use current patterns**: Follow examples from current docs, not training data

## Project-Specific Conventions

### Code Style
- [Language-specific linting rules]
- [Formatting preferences]
- [Naming conventions]

### Testing
- [Testing framework]
- [Test location patterns]
- [Coverage requirements]

### Commits
- Use [Conventional Commits](https://www.conventionalcommits.org/)
- Format: `type(scope): description`
- Types: feat, fix, docs, chore, refactor, test, style

### Documentation
- Update README.md for user-facing changes
- Add ADRs for architectural decisions in `docs/architecture/`
- Keep API docs in sync with code

## Architecture

### Key Components
1. [Component 1]: [Description]
2. [Component 2]: [Description]

### Data Flow
[Brief description of how data flows through the system]

### External Dependencies
- [Dependency 1]: [Version] - [Purpose]
- [Dependency 2]: [Version] - [Purpose]

## Common Tasks

### Development
```bash
# Start development server
[command]

# Run tests
[command]

# Lint code
[command]
```

### Deployment
```bash
# Build for production
[command]

# Deploy
[command]
```

## Gotchas and Constraints

- [Known issue 1]
- [Constraint 1]
- [Important thing to remember]

## Secrets Management

This project uses [secrets-vault](https://github.com/Khamel83/secrets-vault).

**Setup**:
```bash
age --decrypt -i ~/.age/key.txt ~/secrets-vault/secrets.env.encrypted > .env
source .env
```

**Never commit**: `.env`, `secrets.env`, or any file containing actual secrets.

## Resources

- [Internal doc link 1]
- [External resource 1]
```

### Step 5: Create README.md

Generate comprehensive README.md:

```markdown
# [Project Name]

> [One-sentence description]

[Badges: build status, coverage, license, etc.]

## Overview

[2-3 paragraph description of what this project does and why it exists]

## Features

- Feature 1
- Feature 2
- Feature 3

## Prerequisites

- [Tool 1] version X.Y+
- [Tool 2] version X.Y+
- [Required service/dependency]

## Installation

### Quick Start

```bash
# Clone the repository
git clone [repo-url]
cd [project-name]

# Install dependencies
[install command]

# Set up secrets (if applicable)
age --decrypt -i ~/.age/key.txt ~/secrets-vault/secrets.env.encrypted > .env
source .env

# Run
[run command]
```

### Development Setup

```bash
# Install dev dependencies
[dev install command]

# Run tests
[test command]

# Start development server
[dev server command]
```

## Usage

### Basic Usage

```bash
# Example 1
[command and output]

# Example 2
[command and output]
```

### Configuration

[Configuration options and environment variables]

```bash
# Example .env file
KEY=value
```

## Architecture

[Brief architecture overview or link to docs/architecture/]

## Development

### Project Structure

```
[directory tree with explanations]
```

### Running Tests

```bash
# Run all tests
[test command]

# Run specific test
[specific test command]

# Coverage
[coverage command]
```

### Code Style

This project follows [style guide].

```bash
# Lint
[lint command]

# Format
[format command]
```

### Contributing

[Contributing guidelines or link to CONTRIBUTING.md]

## Deployment

[Deployment instructions or link to deployment docs]

## License

[License information]

## Acknowledgments

- [Credit 1]
- [Credit 2]

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### Step 6: Set Up Secrets Management

Integrate secrets-vault:

```bash
# Verify vault exists
if [ ! -d ~/secrets-vault ]; then
    echo "⚠️  Warning: secrets-vault not found at ~/secrets-vault"
    echo "Clone it: git clone https://github.com/Khamel83/secrets-vault.git ~/secrets-vault"
else
    # Decrypt secrets
    age --decrypt -i ~/.age/key.txt ~/secrets-vault/secrets.env.encrypted > .env

    # Create .env.example
    cat .env | awk -F= '{print $1 "="}' > .env.example

    # Verify .env is ignored
    grep -q "^\.env$" .gitignore || echo ".env" >> .gitignore

    echo "✓ Secrets configured"
fi
```

### Step 7: Set Up Quality Tools

Based on project type, set up appropriate tooling:

#### JavaScript/TypeScript
```bash
# Install quality tools
npm install --save-dev \
    eslint prettier \
    @typescript-eslint/parser @typescript-eslint/eslint-plugin \
    jest @types/jest

# Create .eslintrc.js
cat > .eslintrc.js << 'EOF'
module.exports = {
  parser: '@typescript-eslint/parser',
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
  ],
  rules: {
    // Project-specific rules
  }
};
EOF

# Create .prettierrc
cat > .prettierrc << 'EOF'
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5"
}
EOF

# Add npm scripts
npm pkg set scripts.lint="eslint src/**/*.ts"
npm pkg set scripts.format="prettier --write src/**/*.ts"
npm pkg set scripts.test="jest"
```

#### Python
```bash
# Install quality tools
pip install \
    black pylint mypy \
    pytest pytest-cov

# Create pyproject.toml
cat > pyproject.toml << 'EOF'
[tool.black]
line-length = 88
target-version = ['py311']

[tool.pylint]
max-line-length = 88

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
EOF

# Create setup for testing
cat > setup.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name="[project-name]",
    version="0.1.0",
    packages=find_packages(),
)
EOF
```

#### Go
```bash
# Install quality tools
go install golang.org/x/tools/cmd/goimports@latest
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Create .golangci.yml
cat > .golangci.yml << 'EOF'
run:
  deadline: 5m

linters:
  enable:
    - gofmt
    - golint
    - govet
    - errcheck
    - staticcheck
EOF

# Create Makefile
cat > Makefile << 'EOF'
.PHONY: test lint build

test:
	go test -v ./...

lint:
	golangci-lint run

build:
	go build -o bin/app ./cmd/app

fmt:
	gofmt -w .
	goimports -w .
EOF
```

### Step 8: Create Documentation Structure

```bash
# Create docs directory
mkdir -p docs/{architecture,api,guides}

# Create initial architecture doc
cat > docs/architecture/README.md << 'EOF'
# Architecture

## Overview

[System overview]

## Components

### Component 1
[Description]

### Component 2
[Description]

## Data Flow

[Diagrams and descriptions]

## Technology Decisions

See ADRs in this directory for specific decisions.
EOF

# Create ADR template
cat > docs/architecture/adr-template.md << 'EOF'
# ADR-XXX: [Title]

**Date**: YYYY-MM-DD
**Status**: [Proposed | Accepted | Deprecated | Superseded]

## Context

[What is the issue we're facing?]

## Decision

[What is the change we're proposing/making?]

## Consequences

### Positive
- [Benefit 1]

### Negative
- [Trade-off 1]

### Risks
- [Risk 1]

## Alternatives Considered

### Alternative 1
[Description]
**Rejected because**: [Reason]
EOF
```

### Step 9: Set Up CI/CD (Optional)

#### GitHub Actions
```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup
        uses: actions/setup-[language]@v3
        with:
          [language]-version: '[version]'

      - name: Install dependencies
        run: [install command]

      - name: Lint
        run: [lint command]

      - name: Test
        run: [test command]

      - name: Build
        run: [build command]
```

### Step 10: Create Initial Commit

```bash
# Add all files
git add .

# Create comprehensive initial commit
git commit -m "feat: initialize project with ONE_SHOT standards

- Set up project structure
- Add documentation (CLAUDE.md, README.md)
- Configure secrets management
- Set up quality tools ([linter, formatter, tests])
- Add CI/CD pipeline
- Create initial documentation structure

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

## Project Type Templates

### Web Application (React/Next.js)
```
Required:
- package.json with dependencies
- ESLint + Prettier
- Jest or Vitest for testing
- TypeScript configuration
- Environment variables setup
```

### API Service (Express/FastAPI/Go)
```
Required:
- API documentation (OpenAPI/Swagger)
- Authentication/authorization setup
- Database configuration
- Docker Compose for local development
- Health check endpoints
```

### CLI Tool
```
Required:
- Argument parsing setup
- Help documentation
- Man pages or equivalent
- Installation script
- Release automation
```

### Infrastructure Project
```
Required:
- Terraform/Ansible/K8s configs
- State management setup
- Documentation of resources
- Secrets management
- Deployment runbooks
```

## Output Format

After initialization, provide:

```markdown
## ✓ Project Initialized: [Project Name]

**Type**: [Project Type]
**Location**: [Path]

**Created**:
- Directory structure
- CLAUDE.md (project-specific guidance)
- README.md (user documentation)
- .gitignore (security)
- Quality tools ([tools list])
- Documentation structure
- Secrets management
- Initial git commit

**Next Steps**:
1. Review CLAUDE.md for project conventions
2. Install dependencies: `[command]`
3. Set up secrets: `[command]`
4. Run tests: `[command]`
5. Start development: `[command]`

**Documentation**:
- Project guidance: .claude/CLAUDE.md
- User docs: README.md
- Architecture: docs/architecture/
- ADR template: docs/architecture/adr-template.md

**Security**: ✓ .env git-ignored, secrets-vault configured
```

## Best Practices

### Always Include
- CLAUDE.md with project-specific guidance
- Comprehensive README.md
- Proper .gitignore for secrets
- Version-specific dependencies
- Testing framework setup
- Linting/formatting configuration

### Never Include
- Actual secrets or API keys
- Hardcoded credentials
- Generated files (build outputs, dependencies)
- IDE-specific files (unless team uses same IDE)

### Documentation Priority
1. README.md - User-facing, getting started
2. CLAUDE.md - Developer guidance, conventions
3. Architecture docs - System design
4. API docs - Endpoint specifications
5. ADRs - Decision records

## Questions to Ask

1. **Project name and purpose**?
2. **Technology stack** (languages, frameworks)?
3. **Project type** (web app, API, CLI, infrastructure)?
4. **Team size** (solo, small team, large team)?
5. **Deployment target** (local, cloud, hybrid)?
6. **Testing requirements** (unit, integration, E2E)?
7. **CI/CD needed**?
8. **Documentation level** (minimal, standard, comprehensive)?

## Keywords

initialize project, bootstrap project, new project, start project, project setup, scaffold project, create project structure, ONE_SHOT standards

## Resources

- [ONE_SHOT Repository](https://github.com/khamel83/oneshot)
- [Secrets Vault](https://github.com/Khamel83/secrets-vault)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [12 Factor App](https://12factor.net/)
