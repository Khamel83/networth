# Central Secrets - The ONE_SHOT Way

**Philosophy**: ONE place for ALL secrets. Update once, every project gets it.

---

## Setup (One-Time, 5 Minutes)

### Step 1: Install SOPS and age

```bash
# Mac
brew install sops age

# Linux
sudo apt install age
wget https://github.com/getsops/sops/releases/latest/download/sops-v3.8.1.linux.amd64 -O /usr/local/bin/sops
chmod +x /usr/local/bin/sops
```

### Step 2: Generate age Key

```bash
# Create age key (your encryption key for ALL projects)
mkdir -p ~/.config/sops/age
age-keygen -o ~/.config/sops/age/keys.txt

# Output shows your public key:
# Public key: age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**🚨 CRITICAL**: Back up this key to 1Password NOW
- Open 1Password
- Create Secure Note titled "SOPS age encryption key"
- Paste contents of `~/.config/sops/age/keys.txt`
- **Without this key, you can't decrypt your secrets!**

### Step 3: Create Central Secrets Repo

```bash
# 1. Create directory
mkdir -p ~/secrets-vault
cd ~/secrets-vault

# 2. Create SOPS config
# Get your public key first:
grep 'public key' ~/.config/sops/age/keys.txt

# Create .sops.yaml (replace age1xxx... with YOUR public key)
cat > .sops.yaml << 'EOF'
creation_rules:
  - path_regex: .*\.env\.encrypted$
    age: age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF

# 3. Create your secrets file
cat > secrets.env << 'EOF'
# ============================================================================
# ONE_SHOT Central Secrets
# This is the ONLY place you store secrets
# ============================================================================

# OpenRouter (AI - used by all projects)
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here

# GitHub (for automation)
GITHUB_TOKEN=ghp_your-actual-token-here

# Firecrawl (if using)
FIRECRAWL_API_KEY=fc-your-actual-key-here

# Add any other secrets you use
# These are available to ALL your ONE_SHOT projects
EOF

# 4. Encrypt the secrets
sops --encrypt secrets.env > secrets.env.encrypted

# 5. DELETE plaintext (critical!)
rm secrets.env

# 6. Create .gitignore
cat > .gitignore << 'EOF'
# Never commit plaintext
*.env
!*.env.encrypted
EOF

# 7. Create private GitHub repo
git init
git add .
git commit -m "Central secrets vault"
gh repo create secrets-vault --private --source=. --push

# 8. Get your repo URL
git remote get-url origin
# This is your SECRETS_REPO_URL for Q14
```

**You're done!** Your secrets are now:
- ✅ Encrypted
- ✅ Backed up on GitHub (private repo)
- ✅ Available to all your projects

---

## Daily Usage

### Starting a New Project

When ONE_SHOT asks Q14, provide your secrets repo URL:
```
git@github.com:YOUR_USERNAME/secrets-vault.git
```

ONE_SHOT will create `scripts/setup_secrets.sh` that automatically:
1. Clones your secrets repo to `~/.secrets-vault`
2. Decrypts `secrets.env.encrypted` to `.env`
3. Ready to use!

### Working on Existing Project

```bash
# Just run:
./scripts/setup_secrets.sh

# Automatically:
# - Clones/updates central repo
# - Decrypts secrets
# - Creates .env locally
```

### On a New Machine

```bash
# 1. Restore age key from 1Password
mkdir -p ~/.config/sops/age
# Paste key into ~/.config/sops/age/keys.txt

# 2. Clone any project
git clone https://github.com/you/your-project
cd your-project

# 3. Setup secrets
./scripts/setup_secrets.sh

# Done! Secrets pulled from central repo, ready to work
```

### Updating Secrets

```bash
# From ANY project directory:
./scripts/update_secrets.sh

# This will:
# 1. Open secrets.env.encrypted in your editor (decrypted)
# 2. Let you make changes
# 3. Re-encrypt on save
# 4. Commit and push to central repo

# All projects get updated secrets next time they run setup_secrets.sh
```

**Or edit manually**:
```bash
cd ~/.secrets-vault
sops secrets.env.encrypted  # Opens decrypted, saves encrypted
git add secrets.env.encrypted
git commit -m "Update OpenRouter key"
git push
```

---

## How It Works

```
┌─────────────────────────────────────┐
│  github.com/you/secrets-vault       │
│  - secrets.env.encrypted            │
│  - .sops.yaml                       │
│  (encrypted, safe to push)          │
└─────────────────┬───────────────────┘
                  │
                  │ git clone (on setup)
                  │ SOPS decrypt (with age key)
                  ↓
      ┌───────────────────────────┐
      │  ~/.secrets-vault          │
      │  (local cache)             │
      └─────────────┬──────────────┘
                    │
      ┌─────────────┼─────────────┬─────────────┐
      ↓             ↓             ↓             ↓
  Project A     Project B     Project C     Project D
  .env (local)  .env (local)  .env (local)  .env (local)
```

**Key points**:
- Central repo on GitHub (encrypted, backed up)
- Cloned to `~/.secrets-vault` once
- Each project gets `.env` from central repo
- Update central repo → all projects get updates

---

## What Gets Committed to Git

```
✅ CENTRAL REPO (secrets-vault):
- secrets.env.encrypted    (encrypted secrets)
- .sops.yaml               (SOPS config with public key)
- .gitignore

✅ PROJECT REPOS:
- scripts/setup_secrets.sh (pulls from central)
- scripts/update_secrets.sh (edits central)
- .gitignore               (ignores .env)

❌ NEVER COMMIT:
- .env (plaintext secrets)
- ~/.config/sops/age/keys.txt (private key)
```

---

## Troubleshooting

### "Failed to clone secrets repo"

**Problem**: Can't access secrets-vault repo

**Fix**:
```bash
# Login to GitHub
gh auth login

# Verify access
gh repo view YOUR_USERNAME/secrets-vault
```

### "Failed to decrypt secrets"

**Problem**: Age key doesn't match

**Fix**:
```bash
# Check your public key
grep 'public key' ~/.config/sops/age/keys.txt

# Compare with .sops.yaml in central repo
cat ~/.secrets-vault/.sops.yaml

# If different, you need to restore the correct key from 1Password
```

### "age key not found"

**Problem**: Missing age key on new machine

**Fix**:
```bash
# Restore from 1Password
mkdir -p ~/.config/sops/age
# Paste your age key (private + public) into:
# ~/.config/sops/age/keys.txt
```

### "No secrets.env.encrypted found"

**Problem**: Central repo structure wrong

**Fix**:
```bash
cd ~/.secrets-vault
ls -la
# Should have: secrets.env.encrypted, .sops.yaml

# If missing, recreate (see Setup section)
```

---

## Security Model

**What's secure**:
- ✅ Age key in 1Password (encrypted vault)
- ✅ Secrets repo on GitHub (SOPS-encrypted)
- ✅ Local `~/.secrets-vault` (encrypted, only decrypted in memory)

**Attack scenarios**:
- ❌ Someone steals your GitHub password → Can't decrypt (no age key)
- ❌ Someone steals `secrets.env.encrypted` → Can't decrypt (no age key)
- ✅ Only with BOTH GitHub access AND age key can they decrypt

**Best practices**:
- Keep age key in 1Password only
- Don't share age key (even in private messages)
- Use different keys for work vs personal (optional)
- Rotate secrets periodically

---

## Adding New Secrets

```bash
# 1. Edit central repo
cd ~/.secrets-vault
sops secrets.env.encrypted

# 2. Add new secret
# STRIPE_SECRET_KEY=sk_test_...

# 3. Save and close (auto-encrypts)

# 4. Commit and push
git add secrets.env.encrypted
git commit -m "Add Stripe key"
git push

# 5. Update any project
cd ~/projects/any-project
./scripts/setup_secrets.sh  # Gets new Stripe key
```

---

## Cost: $0

Everything is free:
- ✅ SOPS: Open-source
- ✅ age: Open-source
- ✅ GitHub private repo: Free
- ✅ 1Password: (you already have it)

---

## Summary

**One-time setup**:
1. Generate age key → back up to 1Password
2. Create secrets-vault repo (encrypted)
3. Push to private GitHub repo

**Every project**:
1. Provide secrets repo URL in Q14
2. Run `./scripts/setup_secrets.sh`
3. Secrets available in `.env`

**Update secrets**:
1. Run `./scripts/update_secrets.sh` from any project
2. Edit, save, commit, push
3. All projects get updates

**New machine**:
1. Restore age key from 1Password
2. Clone project
3. Run `./scripts/setup_secrets.sh`

**Result**: ONE place for secrets, works everywhere, never lose them.
