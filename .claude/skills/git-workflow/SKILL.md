---
name: git-workflow
description: Automates git operations including conventional commits, branch management, and PR creation. Follows best practices for commit messages, branching strategy, and pull request workflows.
version: "1.0.0"
allowed-tools: [Bash, Read, Grep]
---

# Git Workflow

You are an expert at git workflows, commit conventions, and pull request best practices.

## When to Use This Skill

- User asks to "commit changes" or "create a commit"
- User wants to "create a PR" or "make a pull request"
- User mentions "conventional commits" or "commit message"
- User asks about branching or "create a branch"
- Git workflow automation needed

## Conventional Commits

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring (no feature or bug fix)
- **test**: Adding or updating tests
- **chore**: Maintenance tasks (deps, config)
- **perf**: Performance improvement
- **ci**: CI/CD changes

### Examples

```bash
# New feature
feat(auth): add JWT authentication

# Bug fix
fix(api): handle null response from database

# Documentation
docs(readme): update installation instructions

# Refactoring
refactor(user-service): simplify validation logic

# Multiple files
feat(api): add user management endpoints

- Add POST /api/users
- Add GET /api/users/:id
- Add PUT /api/users/:id
- Add DELETE /api/users/:id
```

## Commit Workflow

### 1. Review Changes

```bash
# Check status
git status

# See diff
git diff

# See staged diff
git diff --cached
```

### 2. Stage Files

```bash
# Stage specific files
git add path/to/file1 path/to/file2

# Stage all changes (careful!)
git add .

# Interactive staging
git add -p
```

### 3. Create Commit

```bash
# Commit with message
git commit -m "$(cat <<'EOF'
type(scope): description

Detailed explanation if needed.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### 4. Push Changes

```bash
# Push to remote
git push origin branch-name

# Push new branch
git push -u origin branch-name
```

## Branch Management

### Branching Strategy

```bash
# Create feature branch
git checkout -b feature/feature-name

# Create fix branch
git checkout -b fix/bug-description

# Create docs branch
git checkout -b docs/update-description
```

### Branch Naming

- **feature/**: New features (`feature/user-auth`)
- **fix/**: Bug fixes (`fix/login-error`)
- **docs/**: Documentation (`docs/api-guide`)
- **refactor/**: Code refactoring (`refactor/user-service`)
- **test/**: Test additions (`test/api-coverage`)
- **chore/**: Maintenance (`chore/update-deps`)

## Pull Request Workflow

### 1. Prepare Branch

```bash
# Ensure branch is up to date
git checkout main
git pull
git checkout feature/my-feature
git rebase main

# Or merge
git merge main
```

### 2. Review Commit History

```bash
# View commits
git log --oneline main..HEAD

# View full diff
git diff main...HEAD
```

### 3. Create PR

```bash
# Using GitHub CLI
gh pr create --title "feat: Add feature name" --body "$(cat <<'EOF'
## Summary
- Change 1
- Change 2
- Change 3

## Test Plan
- [ ] Test case 1
- [ ] Test case 2

## Related Issues
Closes #123

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### PR Template

```markdown
## Summary

Brief description of changes.

## Changes
- Change 1
- Change 2
- Change 3

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Test Plan
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally

## Screenshots (if applicable)

[Add screenshots]

## Related Issues

Closes #[issue number]

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Common Operations

### Amend Last Commit

```bash
# Add forgotten files
git add forgotten-file.txt
git commit --amend --no-edit

# Change commit message
git commit --amend -m "new message"
```

### Squash Commits

```bash
# Interactive rebase
git rebase -i HEAD~3

# Mark commits as 'squash' or 's'
# Save and edit commit message
```

### Cherry-Pick

```bash
# Apply specific commit to current branch
git cherry-pick commit-hash
```

### Stash Changes

```bash
# Stash current changes
git stash

# Apply stashed changes
git stash pop

# List stashes
git stash list
```

## Best Practices

### Commit Messages
- ✅ Use present tense: "add feature" not "added feature"
- ✅ Be specific: "fix null pointer in user service" not "fix bug"
- ✅ Include context in body for complex changes
- ✅ Reference issues: "Closes #123"
- ❌ Avoid vague messages: "update", "fix stuff", "WIP"

### Commits
- ✅ Make atomic commits (one logical change)
- ✅ Commit frequently during development
- ✅ Don't commit commented-out code
- ✅ Don't commit secrets or credentials
- ❌ Avoid large commits with many unrelated changes

### Branches
- ✅ Use descriptive branch names
- ✅ Keep branches short-lived
- ✅ Delete merged branches
- ✅ Rebase or merge from main frequently
- ❌ Don't commit directly to main/master

### Pull Requests
- ✅ Keep PRs focused and small
- ✅ Write descriptive PR descriptions
- ✅ Respond to review feedback promptly
- ✅ Update branch before requesting review
- ❌ Don't create massive PRs (>500 lines)

## Security Checks

Before committing:

```bash
# Check for secrets
git diff | grep -iE "api[_-]?key|secret|password|token"

# Check .gitignore
cat .gitignore | grep -E "\.env|secrets|key"

# Verify no secrets in history
git log -p | grep -iE "api[_-]?key|secret" || echo "No secrets found"
```

## Keywords

commit, git commit, conventional commits, create PR, pull request, branch, git workflow, push changes

## Resources

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Best Practices](https://git-scm.com/book/en/v2)
