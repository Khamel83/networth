# Sharing ONE_SHOT or Parts of It

**Your question**: "How can I share this repo or parts of it (especially SOPS) for work projects?"

---

## GitHub Sharing Options for Private Repos

Your ONE_SHOT repo is private: https://github.com/Khamel83/oneshot

### Option 1: Share Specific Files via Gist (Recommended)

**Best for**: Sharing SOPS guide with coworkers

```bash
# Create a public gist from specific file
gh gist create SOPS_STANDALONE.md --public

# Or private gist (only people with link can see)
gh gist create SOPS_STANDALONE.md --secret
```

**Pros**:
- ✅ People can view without GitHub account
- ✅ Syntax highlighting
- ✅ Can update gist, link stays same
- ✅ No access to your private repo

**Example**: https://gist.github.com/your-username/abc123

### Option 2: Share Raw File URL (While Logged In)

GitHub private repos are readable via URL **if you're logged in**:

```
https://raw.githubusercontent.com/Khamel83/oneshot/master/SOPS_STANDALONE.md
```

**Pros**:
- ✅ Direct link to file
- ✅ Always up-to-date

**Cons**:
- ❌ Requires GitHub login
- ❌ Recipient needs repo access

### Option 3: Invite Collaborators

Add specific people to your private repo:

```bash
# Add collaborator
gh repo edit Khamel83/oneshot --add-collaborator coworker-username

# Or via web: Settings → Collaborators → Add people
```

**Pros**:
- ✅ They see entire repo
- ✅ Can pull/clone normally

**Cons**:
- ❌ Full repo access (not just SOPS doc)

### Option 4: Make Repo Public

If you're comfortable making ONE_SHOT public:

```bash
gh repo edit Khamel83/oneshot --visibility public
```

**Then anyone can view**:
- https://github.com/Khamel83/oneshot
- https://github.com/Khamel83/oneshot/blob/master/SOPS_STANDALONE.md

**Pros**:
- ✅ No login needed
- ✅ Easy to share
- ✅ Contributes to open-source

**Cons**:
- ❌ Everything is public

---

## Recommended Workflow for Work Projects

### For Sharing SOPS Guide

**Create a public gist**:

```bash
cd ~/dev/oneshot
gh gist create SOPS_STANDALONE.md --public --desc "SOPS per-project setup guide"
```

**Then share the gist URL** with coworkers. They can:
- View in browser (no GitHub account needed)
- Copy-paste commands
- See syntax highlighting

### For Sharing Entire ONE_SHOT

**Option A: Make oneshot repo public**
- Good if you want to share with broader community
- Anyone can use it

**Option B: Fork for work**
- Create work-specific fork
- Customize for work environment
- Keep personal one private

```bash
# Create work version
cd ~/dev
cp -r oneshot oneshot-work
cd oneshot-work
rm -rf .git
git init
git add .
git commit -m "ONE_SHOT for work projects"
gh repo create oneshot-work --public --source=. --push
```

---

## Quick Copy-Paste SOPS for Work

If you just need to give coworkers SOPS instructions:

**1. Send them SOPS_STANDALONE.md as gist**:
```bash
cd ~/dev/oneshot
gh gist create SOPS_STANDALONE.md --public
```

**2. Or create a simple README**:

```markdown
# SOPS Quick Setup for Work Projects

## Install
\`\`\`bash
brew install sops age  # Mac
\`\`\`

## Generate Key
\`\`\`bash
mkdir -p ~/.config/sops/age
age-keygen -o ~/.config/sops/age/keys.txt
grep 'public key' ~/.config/sops/age/keys.txt
\`\`\`

## Setup Project
\`\`\`bash
# In your project
cat > .sops.yaml << 'EOF'
creation_rules:
  - path_regex: \.env\.encrypted$
    age: YOUR_PUBLIC_KEY_HERE
EOF

# Create secrets
cat > .env << 'EOF'
API_KEY=your-key
DATABASE_URL=postgresql://...
EOF

# Encrypt
sops --encrypt .env > .env.encrypted
rm .env

# Commit
git add .sops.yaml .env.encrypted
git commit -m "Add encrypted secrets"
\`\`\`

Full guide: [link to gist]
```

---

## Your Secrets-Vault (Already Created!)

Your central secrets repo is ready:
- **URL**: https://github.com/Khamel83/secrets-vault
- **Status**: Private
- **Location**: ~/secrets-vault/
- **Contents**: secrets.env.encrypted (placeholders for now)

### Next Steps:

**1. Back up your age key to 1Password**:
```bash
cat ~/.config/sops/age/keys.txt
# Copy entire contents to 1Password Secure Note
# Title: "SOPS age encryption key"
```

**2. Add real secrets**:
```bash
cd ~/secrets-vault
sops secrets.env.encrypted
# Opens in editor (decrypted)
# Replace placeholder values with real ones
# Save and close (auto-encrypts)
git add secrets.env.encrypted
git commit -m "Add real secrets"
git push
```

**3. Use in ONE_SHOT projects**:
When creating new projects, provide in Q14:
```
git@github.com:Khamel83/secrets-vault.git
```

---

## Summary

| Need | Solution | Public? |
|------|----------|---------|
| Share SOPS guide with coworkers | Create gist of SOPS_STANDALONE.md | Yes/No (your choice) |
| Share entire ONE_SHOT | Make repo public OR create work fork | Your choice |
| Share with specific people | Invite as collaborators | Private stays private |
| View from work computer | GitHub raw URL (requires login) | Private |
| Use SOPS at work | Copy SOPS_STANDALONE.md | Standalone per-project |
| Your personal projects | Use secrets-vault (already created!) | Private |

**My recommendation**:
1. **Keep oneshot repo private** (personal use)
2. **Create public gist of SOPS_STANDALONE.md** (for sharing)
3. **Use secrets-vault for personal projects** (already set up)
4. **Use SOPS_STANDALONE.md pattern for work** (per-project)
