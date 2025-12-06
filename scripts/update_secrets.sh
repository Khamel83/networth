#!/usr/bin/env bash
# scripts/update_secrets.sh - Update secrets in central repo

set -euo pipefail

SECRETS_VAULT_DIR="${HOME}/.secrets-vault"

echo "=== Updating central secrets ==="

# Check if vault exists
if [ ! -d "$SECRETS_VAULT_DIR" ]; then
    echo "❌ No central secrets repo found at $SECRETS_VAULT_DIR"
    echo ""
    echo "Run ./scripts/setup_secrets.sh first to clone it"
    exit 1
fi

cd "$SECRETS_VAULT_DIR"

# Pull latest
echo "🔄 Pulling latest from central repo..."
git pull -q

# Edit encrypted file
echo "📝 Opening secrets.env.encrypted in editor..."
echo "(SOPS will decrypt, let you edit, and re-encrypt on save)"
echo ""

sops secrets.env.encrypted

# Commit changes
echo ""
echo "Commit changes to central repo? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    git add secrets.env.encrypted
    git commit -m "Update secrets"
    git push

    echo ""
    echo "✅ Secrets updated in central repo!"
    echo ""
    echo "To update local .env in this project:"
    echo "  ./scripts/setup_secrets.sh"
else
    echo "Changes not committed. Run manually when ready:"
    echo "  cd $SECRETS_VAULT_DIR"
    echo "  git add secrets.env.encrypted"
    echo "  git commit -m 'Update secrets'"
    echo "  git push"
fi
