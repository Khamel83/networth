---
name: secrets-vault-manager
description: Automates secrets management for any project using the secrets-vault system. Clones the vault, decrypts secrets with age key, and sets up environment variables. Use when user mentions "secrets", "environment variables", "API keys", or "set up secrets-vault".
version: "1.0.0"
allowed-tools: [Bash, Read, Write, Grep]
---

# Secrets Vault Manager

You are an expert at managing secrets using the secrets-vault system (https://github.com/Khamel83/secrets-vault).

## When to Use This Skill

- User says "I use secrets-vault for environment variables"
- User asks to "set up secrets" or "configure secrets"
- User mentions "API keys", "environment variables", or "credentials"
- User says "set up secrets-vault for this project"
- New project initialization that needs secrets
- User mentions "decrypt secrets" or "access vault"

## Secrets-Vault System Overview

**What it is**: A secure, encrypted secrets management system
- **Private key**: Stored in 1Password (age encryption key)
- **Encrypted secrets**: Stored in `secrets.env.encrypted` in public repo
- **Repository**: https://github.com/Khamel83/secrets-vault
- **Public but secure**: Repo is public; only private key can decrypt

**How it works**:
1. User has age private key (already configured)
2. Secrets are encrypted in `secrets.env.encrypted`
3. Projects clone vault and decrypt secrets locally
4. Decrypted secrets become environment variables

## Setup Workflow

### Step 1: Verify Age Key Exists

Check if user has age key configured:
```bash
# Check for age key
ls -la ~/.age/

# Or check if age is installed
which age
```

**Expected**: User already has age key set up.

### Step 2: Clone Secrets Vault (If Not Present)

Check if secrets-vault exists locally:
```bash
# Check for vault directory
if [ ! -d ~/secrets-vault ]; then
    echo "Cloning secrets-vault..."
    git clone https://github.com/Khamel83/secrets-vault.git ~/secrets-vault
else
    echo "Secrets vault already exists"
fi
```

### Step 3: Set Up Project

The README.md in secrets-vault contains 3 commands to run. Execute them:

```bash
# Navigate to project directory
cd /path/to/project

# Command 1: Decrypt secrets
age --decrypt -i ~/.age/key.txt ~/secrets-vault/secrets.env.encrypted > .env

# Command 2: Source environment variables
source .env

# Command 3: Verify secrets loaded
printenv | grep -E "API|KEY|SECRET|TOKEN" | head -5
```

### Step 4: Add .env to .gitignore

**CRITICAL SECURITY STEP**: Never commit decrypted secrets!

```bash
# Check if .env is in .gitignore
if ! grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo ".env" >> .gitignore
    echo "Added .env to .gitignore"
fi

# Also add common secret files
if ! grep -q "^secrets\.env$" .gitignore 2>/dev/null; then
    echo "secrets.env" >> .gitignore
fi

# Verify
cat .gitignore | grep -E "\.env|secrets"
```

### Step 5: Verify Setup

Confirm secrets are available:
```bash
# Show that environment variables are loaded (without revealing values)
echo "Checking environment variables..."
printenv | grep -E "API|KEY|SECRET|TOKEN" | awk -F= '{print $1 " = [REDACTED]"}' | head -10
```

### Step 6: Document Usage

Create or update project documentation:
```markdown
## Secrets Management

This project uses [secrets-vault](https://github.com/Khamel83/secrets-vault) for secure secrets management.

### Initial Setup

```bash
# Decrypt secrets (requires age key in 1Password)
age --decrypt -i ~/.age/key.txt ~/secrets-vault/secrets.env.encrypted > .env

# Source environment variables
source .env

# Verify (shows variable names only, not values)
printenv | grep -E "API|KEY|SECRET|TOKEN" | awk -F= '{print $1}'
```

### Daily Usage

```bash
# Load secrets in new terminal session
source .env
```

### Security Notes

- `.env` file is git-ignored (never committed)
- Private age key stored in 1Password
- Encrypted vault is public (safe to share)
```

## Common Operations

### Operation 1: Initial Project Setup

**User says**: "Set up secrets-vault for this project"

**Actions**:
1. Verify age key exists
2. Clone secrets-vault if needed
3. Decrypt secrets to `.env`
4. Add `.env` to `.gitignore`
5. Document usage in README

### Operation 2: Refresh Secrets

**User says**: "Refresh my secrets" or "Update environment variables"

**Actions**:
```bash
# Re-decrypt secrets (in case vault was updated)
age --decrypt -i ~/.age/key.txt ~/secrets-vault/secrets.env.encrypted > .env

# Source updated variables
source .env

echo "Secrets refreshed"
```

### Operation 3: Verify Secrets Access

**User says**: "Check if secrets are loaded" or "Verify environment variables"

**Actions**:
```bash
# Show available secret variables (names only)
printenv | grep -E "API|KEY|SECRET|TOKEN" | awk -F= '{print "✓ " $1}'
```

### Operation 4: Add to New Project

**User says**: "Initialize secrets for new project"

**Actions**:
1. Run full setup workflow
2. Add secrets documentation to project README
3. Create example `.env.example` with variable names (no values)

```bash
# Generate .env.example
printenv | grep -E "API|KEY|SECRET|TOKEN" | awk -F= '{print $1 "="}' > .env.example
```

### Operation 5: CI/CD Integration

**User asks**: "How do I use secrets in CI/CD?"

**Guidance**:
```markdown
For CI/CD pipelines:

1. **GitHub Actions**: Store age key in repository secrets
   ```yaml
   - name: Decrypt secrets
     run: |
       echo "${{ secrets.AGE_KEY }}" > key.txt
       age --decrypt -i key.txt secrets.env.encrypted > .env
       source .env
   ```

2. **GitLab CI**: Use CI/CD variables
3. **Docker**: Use build secrets or environment variables
```

## Security Best Practices

### Never Commit These Files
```
.env
.env.local
.env.production
secrets.env
key.txt
*.key
*_key
```

### Always Git-Ignore
```gitignore
# Secrets
.env*
!.env.example
secrets.env
secrets.*.env

# Keys
*.key
*_key
key.txt
```

### Rotation Strategy
```markdown
When rotating secrets:
1. Update values in secrets-vault repo
2. Re-encrypt: `age --encrypt -r [public-key] secrets.env > secrets.env.encrypted`
3. Commit encrypted file
4. Push to GitHub
5. Team members run: `age --decrypt -i ~/.age/key.txt ~/secrets-vault/secrets.env.encrypted > .env`
```

## Troubleshooting

### Issue: "age: error: no identity matched any recipient"

**Cause**: Wrong age key or corrupted encryption

**Solution**:
```bash
# Verify age key
cat ~/.age/key.txt

# Try re-cloning vault
rm -rf ~/secrets-vault
git clone https://github.com/Khamel83/secrets-vault.git ~/secrets-vault

# Attempt decrypt again
age --decrypt -i ~/.age/key.txt ~/secrets-vault/secrets.env.encrypted > .env
```

### Issue: "age: command not found"

**Cause**: age not installed

**Solution**:
```bash
# macOS
brew install age

# Linux (Debian/Ubuntu)
apt-get install age

# Linux (Arch)
pacman -S age
```

### Issue: Environment variables not available

**Cause**: `.env` not sourced in current shell

**Solution**:
```bash
# Source in current shell
source .env

# Or export manually
export $(cat .env | xargs)

# Verify
printenv | grep API_KEY
```

### Issue: Secrets work locally but not in Docker

**Cause**: Docker container doesn't have access to `.env`

**Solution**:
```dockerfile
# Option 1: Build-time secrets
RUN --mount=type=secret,id=env \
    cat /run/secrets/env > .env

# Option 2: Runtime environment variables
docker run --env-file .env myapp

# Option 3: Docker Compose
services:
  app:
    env_file:
      - .env
```

## Integration with Project Types

### Node.js/JavaScript
```javascript
// Load environment variables
require('dotenv').config();

// Access secrets
const apiKey = process.env.API_KEY;
```

```bash
# Install dotenv
npm install dotenv
```

### Python
```python
# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Access secrets
import os
api_key = os.getenv('API_KEY')
```

```bash
# Install python-dotenv
pip install python-dotenv
```

### Go
```go
// Load environment variables
import "github.com/joho/godotenv"

func init() {
    godotenv.Load()
}

// Access secrets
import "os"
apiKey := os.Getenv("API_KEY")
```

```bash
# Install godotenv
go get github.com/joho/godotenv
```

### Docker Compose
```yaml
services:
  app:
    env_file:
      - .env
    environment:
      - API_KEY=${API_KEY}
```

### Shell Scripts
```bash
#!/bin/bash

# Load secrets
if [ -f .env ]; then
    source .env
else
    echo "ERROR: .env not found. Run setup first."
    exit 1
fi

# Use secrets
curl -H "Authorization: Bearer $API_KEY" https://api.example.com
```

## Output Format

After setting up secrets-vault, provide:

```markdown
## ✓ Secrets Vault Setup Complete

**Location**: ~/secrets-vault
**Decrypted to**: .env (git-ignored)

**Available Secrets**:
- API_KEY_1
- API_KEY_2
- DATABASE_URL
- [etc...]

**Usage**:
```bash
# Load secrets in new terminal
source .env
```

**Next Steps**:
1. Secrets are ready to use
2. `.env` is git-ignored (verified)
3. Documentation added to README

**Security**: ✓ Private key secure, .env not committed
```

## Questions to Ask Users

1. Is this a new project or existing project?
2. What programming language/framework? (affects .env loading method)
3. Do you need CI/CD integration?
4. Should I document secrets setup in the README?
5. Do you need a `.env.example` template?

## Keywords

secrets, secrets-vault, environment variables, API keys, credentials, age encryption, decrypt secrets, set up secrets, configure secrets, .env file

## Resources

- [Secrets Vault Repository](https://github.com/Khamel83/secrets-vault)
- [Age Encryption](https://github.com/FiloSottile/age)
- [Environment Variables Best Practices](https://12factor.net/config)

## Examples

### Example 1: New Project Setup

**User**: "Set up secrets-vault for this new API project"

**Actions**:
```bash
# 1. Verify vault exists
ls ~/secrets-vault || git clone https://github.com/Khamel83/secrets-vault.git ~/secrets-vault

# 2. Decrypt secrets
age --decrypt -i ~/.age/key.txt ~/secrets-vault/secrets.env.encrypted > .env

# 3. Add to gitignore
echo ".env" >> .gitignore

# 4. Source secrets
source .env

# 5. Verify
printenv | grep API | awk -F= '{print "✓ " $1}'
```

**Output**: "✓ Secrets configured. All API keys available as environment variables."

### Example 2: Existing Project

**User**: "This project needs secrets. Use secrets-vault."

**Actions**:
```bash
# Check if already set up
if [ -f .env ]; then
    echo "Secrets already configured"
    source .env
else
    # Run full setup
    age --decrypt -i ~/.age/key.txt ~/secrets-vault/secrets.env.encrypted > .env
    echo ".env" >> .gitignore
    source .env
fi
```

**Output**: "✓ Secrets loaded. Ready to use."
