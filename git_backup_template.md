# ONE_SHOT Commit Message Templates

## Purpose
Use these templates to save your work before switching branches or when collaborating with others.

## Before Branch Switching
```bash
# Commit current work as backup
git add .
git commit -m "$(cat <<'EOF'
backup: Save ONE_SHOT v1.7 enhancements before branch changes

- Protected Q2.5 Reality Check with stronger validation
- Added Required Observability with status scripts and health endpoints
- Enhanced Three-Tier AI Strategy for cost-conscious development
- Integrated comprehensive SOPS + Age secrets management
- Added Validation-Before-Build to prevent wasted effort
- Enhanced Future-You Documentation with WHY standards
- Added Claude Skills Integration making ONE_SHOT machine-readable

All changes based on 8 real-world projects (135K+ records, $1-3/month AI costs)
EOF
)"
git push origin backup-my-oneshot-v1.7
```

## Protecting Your Work
```bash
# When switching to work on shared documents:
git checkout -b your-feature-branch
git checkout master
git pull origin master
git merge your-feature-branch

# This creates a merge commit that preserves both versions
git push origin master

# Then create a Pull Request for review
# Your work is safely backed up on your feature branch
```

## Collaboration Best Practices
```bash
# Use descriptive commit messages
git commit -m "feat: enhance Reality Check validation"

# Reference issues in commits
git commit -m "fix: resolve database locking issue (#123)"

# Communicate before big changes
# Open issue: "Planning major changes to storage layer"

# Use feature branches for experimental work
git checkout -b experiment/new-approach
```

## Emergency Recovery
```bash
# If work gets overwritten:
git reflog --oneline -10  # See last 10 commits
git checkout HEAD@{commit-hash}  # Go back to before overwrite
git cherry-pick {commit-hash}  # Restore specific commit
```

Use these templates to ensure your valuable work is never lost!