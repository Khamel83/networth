#!/usr/bin/env bash
# scripts/setup_secrets.sh - Pull secrets from central repo

set -euo pipefail

echo "=== Setting up secrets from central repo ==="

# Configuration (will be set by ONE_SHOT during project creation)
SECRETS_REPO_URL="${SECRETS_REPO_URL:-SECRETS_REPO_URL_PLACEHOLDER}"
SECRETS_VAULT_DIR="${HOME}/.secrets-vault"

# Check if SOPS is installed
if ! command -v sops &> /dev/null; then
    echo "❌ SOPS not installed"
    echo ""
    echo "Install with:"
    echo "  Mac:   brew install sops age"
    echo "  Linux: sudo apt install age && wget https://github.com/getsops/sops/releases/latest/download/sops-v3.8.1.linux.amd64 -O /usr/local/bin/sops && chmod +x /usr/local/bin/sops"
    exit 1
fi

# Check if age key exists
if [ ! -f ~/.config/sops/age/keys.txt ]; then
    echo "❌ age key not found at ~/.config/sops/age/keys.txt"
    echo ""
    echo "Restore from 1Password or generate new:"
    echo "  mkdir -p ~/.config/sops/age"
    echo "  age-keygen -o ~/.config/sops/age/keys.txt"
    exit 1
fi

# Clone or update central secrets repo
if [ ! -d "$SECRETS_VAULT_DIR" ]; then
    echo "📥 Cloning central secrets repo..."

    if ! git clone "$SECRETS_REPO_URL" "$SECRETS_VAULT_DIR" 2>/dev/null; then
        echo "❌ Failed to clone secrets repo: $SECRETS_REPO_URL"
        echo ""
        echo "Make sure:"
        echo "  1. You're logged into GitHub (gh auth login)"
        echo "  2. The repo exists and is accessible"
        echo "  3. The URL is correct"
        exit 1
    fi
else
    echo "🔄 Updating central secrets repo..."
    (cd "$SECRETS_VAULT_DIR" && git pull -q)
fi

# Decrypt secrets
echo "🔓 Decrypting secrets..."

if [ -f "$SECRETS_VAULT_DIR/secrets.env.encrypted" ]; then
    if sops --decrypt "$SECRETS_VAULT_DIR/secrets.env.encrypted" > .env 2>/dev/null; then
        echo "✅ Secrets ready in .env"
        echo ""
        echo "Your .env contains ALL your secrets from central repo"
        echo "Never commit .env to git!"
    else
        echo "❌ Failed to decrypt secrets"
        echo ""
        echo "Check:"
        echo "  1. Your age key matches the one used to encrypt"
        echo "  2. Run: grep 'public key' ~/.config/sops/age/keys.txt"
        exit 1
    fi
else
    echo "❌ No secrets.env.encrypted found in $SECRETS_VAULT_DIR"
    echo ""
    echo "Create your central secrets repo first (see CENTRAL_SECRETS.md)"
    exit 1
fi
