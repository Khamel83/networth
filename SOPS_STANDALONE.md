# SOPS Standalone (Per-Project Pattern)

**Use case**: Work projects where you can't use personal central secrets repo, or projects with project-specific secrets only.

---

## When to Use This vs. Central Secrets

**Use Central Secrets** (default for personal projects):
- Personal projects where you control everything
- Same secrets across multiple projects (OpenRouter, GitHub token)
- Want to update once, all projects get it

**Use Standalone SOPS** (work projects):
- Work projects (can't use personal secrets repo)
- Project has unique secrets not shared with others
- Different team members need access (multiple age keys)
- Project secrets stay in project repo

---

## Quick Setup (5 Minutes)

### 1. Install SOPS and age (if not already done)

```bash
# Mac
brew install sops age

# Linux
sudo apt install age
wget https://github.com/getsops/sops/releases/latest/download/sops-v3.8.1.linux.amd64 -O /usr/local/bin/sops
chmod +x /usr/local/bin/sops
```

### 2. Generate age key (if not already done)

```bash
mkdir -p ~/.config/sops/age
age-keygen -o ~/.config/sops/age/keys.txt

# Get your public key
grep 'public key' ~/.config/sops/age/keys.txt
# age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Back up to 1Password** (if you haven't already)

### 3. Setup SOPS in Your Project

```bash
cd your-project

# Create .sops.yaml
cat > .sops.yaml << 'EOF'
creation_rules:
  - path_regex: \.env\.encrypted$
    age: age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF
# Replace age1xxx with YOUR public key

# Create .env with secrets
cat > .env << 'EOF'
# Project-specific secrets
DATABASE_URL=postgresql://user:pass@localhost/db
API_KEY=your-api-key-here
EOF

# Encrypt it
sops --encrypt .env > .env.encrypted

# Delete plaintext
rm .env

# Add to .gitignore
cat >> .gitignore << 'EOF'

# Secrets
.env
!.env.encrypted
EOF

# Commit encrypted version
git add .env.encrypted .sops.yaml .gitignore
git commit -m "Add encrypted secrets"
```

---

## Daily Workflow

### Decrypt Secrets

```bash
# Create .env from encrypted version
sops --decrypt .env.encrypted > .env

# Or create a script: scripts/setup_secrets.sh
#!/usr/bin/env bash
set -euo pipefail
if [ -f .env.encrypted ]; then
    sops --decrypt .env.encrypted > .env
    echo "✅ Secrets decrypted to .env"
else
    echo "❌ No .env.encrypted found"
    exit 1
fi
```

### Edit Secrets

```bash
# Edit encrypted file directly (SOPS handles decryption)
sops .env.encrypted

# Or manually:
sops --decrypt .env.encrypted > .env
nano .env
sops --encrypt .env > .env.encrypted
rm .env
git add .env.encrypted
git commit -m "Update secrets"
```

### On New Machine

```bash
# 1. Restore age key from 1Password
mkdir -p ~/.config/sops/age
# Paste into ~/.config/sops/age/keys.txt

# 2. Clone project
git clone https://github.com/your/project
cd project

# 3. Decrypt
sops --decrypt .env.encrypted > .env

# Done!
```

---

## Team Projects (Multiple Developers)

If multiple people need access:

```bash
# Each person generates their own age key
age-keygen -o ~/.config/sops/age/keys.txt

# Each person shares their PUBLIC key
grep 'public key' ~/.config/sops/age/keys.txt

# Update .sops.yaml with all public keys
cat > .sops.yaml << 'EOF'
creation_rules:
  - path_regex: \.env\.encrypted$
    age: >-
      age1alice...,
      age1bob...,
      age1charlie...
EOF

# Re-encrypt with all keys
sops updatekeys .env.encrypted

# Now anyone with their own key can decrypt
```

---

## Scripts for Standalone Projects

### scripts/setup_secrets.sh

```bash
#!/usr/bin/env bash
# scripts/setup_secrets.sh - Decrypt secrets for standalone project

set -euo pipefail

echo "=== Setting up secrets (standalone project) ==="

# Check SOPS installed
if ! command -v sops &> /dev/null; then
    echo "❌ SOPS not installed"
    echo "Install: brew install sops age"
    exit 1
fi

# Check age key
if [ ! -f ~/.config/sops/age/keys.txt ]; then
    echo "❌ age key not found"
    echo "Restore from 1Password to ~/.config/sops/age/keys.txt"
    exit 1
fi

# Decrypt
if [ -f .env.encrypted ]; then
    sops --decrypt .env.encrypted > .env
    echo "✅ Secrets decrypted to .env"
else
    echo "❌ No .env.encrypted found"
    echo "Create .env and encrypt with: sops --encrypt .env > .env.encrypted"
    exit 1
fi
```

### scripts/encrypt_secrets.sh

```bash
#!/usr/bin/env bash
# scripts/encrypt_secrets.sh - Encrypt secrets for commit

set -euo pipefail

echo "=== Encrypting secrets ==="

if [ ! -f .env ]; then
    echo "❌ No .env file to encrypt"
    exit 1
fi

# Encrypt
sops --encrypt .env > .env.encrypted
echo "✅ Encrypted to .env.encrypted"

echo ""
echo "Next steps:"
echo "  git add .env.encrypted"
echo "  git commit -m 'Update secrets'"
echo "  git push"
echo ""
echo "⚠️ Don't forget to delete .env after committing!"
```

### scripts/edit_secrets.sh

```bash
#!/usr/bin/env bash
# scripts/edit_secrets.sh - Edit encrypted secrets

set -euo pipefail

if [ ! -f .env.encrypted ]; then
    echo "❌ No .env.encrypted found"
    exit 1
fi

# Edit (SOPS handles decrypt/encrypt)
sops .env.encrypted

# Update local copy
sops --decrypt .env.encrypted > .env

echo "✅ Secrets updated"
echo "Commit changes:"
echo "  git add .env.encrypted"
echo "  git commit -m 'Update secrets'"
```

---

## .gitignore Pattern

```gitignore
# Secrets
.env

# But allow encrypted version
!.env.encrypted
```

---

## Comparison: Central vs. Standalone

| Feature | Central Secrets | Standalone SOPS |
|---------|-----------------|-----------------|
| **Use case** | Personal projects | Work projects, unique secrets |
| **Secrets location** | github.com/you/secrets-vault | Project repo (.env.encrypted) |
| **Setup** | Once (one repo) | Per-project |
| **Sharing secrets** | All projects automatically | Only this project |
| **Update secrets** | Once, all projects get it | Only this project |
| **Team access** | Your key only | Multiple keys (team) |
| **Complexity** | Simplest | Simple |

---

## Copy-Paste Setup for Work Project

```bash
# In your work project directory

# 1. Create .sops.yaml (use YOUR public key)
grep 'public key' ~/.config/sops/age/keys.txt
cat > .sops.yaml << 'EOF'
creation_rules:
  - path_regex: \.env\.encrypted$
    age: YOUR_PUBLIC_KEY_HERE
EOF

# 2. Create .env with project secrets
cat > .env << 'EOF'
DATABASE_URL=postgresql://...
API_KEY=...
EOF

# 3. Encrypt
sops --encrypt .env > .env.encrypted
rm .env

# 4. Ignore plaintext
echo ".env" >> .gitignore
echo "!.env.encrypted" >> .gitignore

# 5. Commit
git add .sops.yaml .env.encrypted .gitignore
git commit -m "Add encrypted secrets"
git push

# 6. On other machines: sops --decrypt .env.encrypted > .env
```

---

## Troubleshooting

### "Failed to get the data key"

Your age key doesn't match. Check:
```bash
grep 'public key' ~/.config/sops/age/keys.txt
cat .sops.yaml
```

If they don't match, you need the original key OR re-encrypt with your key.

### "age: no identity matched"

SOPS can't find your age key:
```bash
ls ~/.config/sops/age/keys.txt
export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt
```

---

## Summary

**Central Secrets** (ONE_SHOT default):
- One repo for all personal project secrets
- Simplest for personal use

**Standalone SOPS** (this guide):
- Per-project encrypted secrets
- Use for work or project-specific secrets
- Copy-paste setup from this doc

Both use the same age key, so you're already set up!
