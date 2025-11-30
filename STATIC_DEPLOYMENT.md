# NET WORTH Static Deployment Guide

This guide covers the complete deployment process for the NET WORTH static tennis ladder system.

## Architecture Overview

The NET WORTH static system consists of:
- **Data Layer**: TOML files in `data/` directory
- **Processing Layer**: Python scripts for ladder computation and pairings
- **Automation Layer**: GitHub Actions for scheduled updates
- **Frontend Layer**: Static HTML/JS served by Vercel
- **Secrets Management**: Integration with secrets-vault for sensitive data

## Operator Runbook

### Initial Setup

#### 1. Repository Preparation

```bash
# Clone the repository
git clone https://github.com/Khamel83/networth.git
cd networth

# Install Python dependencies
pip install tomli-w tomli  # For TOML processing

# Make scripts executable
chmod +x scripts/*.py
```

#### 2. Bootstrap Data from SQLite

If you have existing data in `networth_tennis.db`:

```bash
# Run bootstrap to convert SQLite to TOML
python scripts/bootstrap_from_sqlite.py --db networth_tennis.db

# This creates:
# - data/players.toml
# - data/matches.toml
```

For fresh deployment without existing data:

```bash
# Create initial players.toml manually
# See DATA_MODEL.md for schema

# Ensure data/league.toml exists with your league info
# Ensure data/courts.toml exists with local court information
```

#### 3. Generate Initial Ladder and Pairings

```bash
# Compute ladder rankings from players + matches
python scripts/recompute_ladder.py --verbose

# Generate weekly pairings
python scripts/generate_pairings.py --verbose

# Export static JSON for frontend
python scripts/export_static_json.py --verbose
```

#### 4. Test Locally

```bash
# Start a simple HTTP server
python -m http.server 8000

# Or use any static server
npx serve .

# Visit http://localhost:8000 to verify ladder loads
# Check browser console for any JSON loading errors
```

### Vercel Deployment

#### 1. Connect Repository to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "New Project"
3. Import the `Khamel83/networth` repository
4. Vercel will auto-detect the static site configuration

#### 2. Configure Vercel Settings

```bash
# Ensure vercel.json is properly configured
# It should route JSON files correctly:

{
  "routes": [
    {
      "src": "/ladder.json",
      "dest": "/ladder.json"
    },
    {
      "src": "/pairings.json",
      "dest": "/pairings.json"
    },
    // ... other JSON routes
  ]
}
```

#### 3. Custom Domain Setup

1. In Vercel dashboard, go to "Domains"
2. Add `networthtennis.com`
3. Configure DNS to point to Vercel:
   - CNAME record: `networthtennis.com` → `cname.vercel-dns.com`

#### 4. Environment Variables (Optional)

If using secrets-vault integration:

```bash
# In Vercel dashboard → Settings → Environment Variables
EMAIL_FROM_ADDRESS=matches@networthtennis.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SECRETS_VAULT_TOKEN=your_token_here
```

### GitHub Actions Setup

#### 1. Enable Actions

```bash
# Ensure .github/workflows/networth_static_pipeline.yml exists
# Push to trigger initial run:

git add .
git commit -m "Setup static pipeline"
git push origin main
```

#### 2. Configure Repository Permissions

In GitHub repository settings:

1. **Actions** → **General**:
   - Allow "Actions" to run
   - Allow "GITHUB_TOKEN" to push changes

2. **Actions** → **General permissions**:
   - Contents: Read and write
   - Actions: Read

#### 3. Manual Trigger for Testing

```bash
# Run workflow manually via GitHub UI:
# Go to Actions → NET WORTH Static Pipeline → "Run workflow"

# Or via GitHub CLI:
gh workflow run networth_static_pipeline.yml
```

### secrets-vault Integration

#### 1. Setup secrets-vault

```bash
# If using Khamel83/secrets-vault:

# Create secrets for the networth project
vault write secret/networth/email \
  from_address="matches@networthtennis.com" \
  smtp_host="smtp.gmail.com" \
  smtp_user="networth@networthtennis.com" \
  smtp_password="app_password"

# Create secrets for API integrations
vault write secret/networth/api \
  weather_api_key="your_key" \
  maps_api_key="your_key"
```

#### 2. Configure GitHub Actions to Access Secrets

```yaml
# In .github/workflows/networth_static_pipeline.yml:

- name: Setup secrets
  run: |
    # Install vault CLI
    # Authenticate and export secrets as environment variables
    export VAULT_ADDR="https://your-vault-server"
    export VAULT_TOKEN="${{ secrets.VAULT_TOKEN }}"

    # Export secrets for scripts
    export EMAIL_PASSWORD=$(vault read -field=password secret/networth/email)
```

### Regular Operations

#### Weekly Ladder Updates

The GitHub Action runs automatically every Monday at 1:00 UTC (Sunday 6:00 PM PT):

1. **Recomputes ladder**: Updates rankings from all matches
2. **Generates pairings**: Creates new weekly matches
3. **Exports JSON**: Updates frontend data files
4. **Commits changes**: Auto-commits updated files to repository

#### Manual Data Updates

```bash
# To add new matches manually:
# 1. Edit data/matches.toml
# 2. Run: python scripts/recompute_ladder.py
# 3. Run: python scripts/export_static_json.py
# 4. Commit: git add data/ public/ && git commit -m "Add new matches"

# To update player availability:
# 1. Edit data/players.toml
# 2. Run: python scripts/generate_pairings.py
# 3. Run: python scripts/export_static_json.py
# 4. Commit changes
```

#### Adding New Players

```bash
# 1. Add player to data/players.toml
[[players]]
id = "new_player_id"
name = "New Player Name"
email = "player@email.com"
active = true
initial_rating = 1500
preferred_courts = ["vermont_canyon"]

[players.availability]
mon_evening = true
# ... set availability

# 2. Recompute ladder
python scripts/recompute_ladder.py

# 3. Regenerate pairings
python scripts/generate_pairings.py

# 4. Export static JSON
python scripts/export_static_json.py

# 5. Commit changes
git add data/ public/ && git commit -m "Add new player"
```

### Troubleshooting

#### GitHub Actions Fails

```bash
# Check workflow logs at:
# https://github.com/Khamel83/networth/actions

# Common issues:
# - Missing TOML files: Run bootstrap script
# - Permission denied: Check repository permissions
# - Secrets not found: Verify secrets-vault setup
```

#### Frontend JSON Loading Errors

```bash
# Check browser console for specific errors
# Verify JSON files exist in public/ directory
ls -la public/

# Test JSON files manually:
curl https://networthtennis.com/ladder.json
curl https://networthtennis.com/pairings.json
```

#### Ladder Rankings Not Updating

```bash
# Check if matches.toml has data
python -c "import tomllib; print(len(tomllib.load(open('data/matches.toml', 'rb')).get('matches', [])))"

# Manually recompute ladder
python scripts/recompute_ladder.py --verbose

# Verify ladder_snapshot.toml was updated
head -n 20 data/ladder_snapshot.toml
```

#### Pairings Generation Issues

```bash
# Check player availability data
python -c "import tomllib; data=tomllib.load(open('data/players.toml','rb')); print([p['name'] for p in data['players'] if not p.get('availability')])"

# Manually generate pairings with debug output
python scripts/generate_pairings.py --verbose
```

### Maintenance Tasks

#### Monthly

```bash
# Review and archive old matches
# Keep last 6 months of detailed data, older matches as summaries

# Update courts.toml if any new courts added
# Review league configuration in league.toml

# Backup data directory
cp -r data/ data_backup_$(date +%Y%m)/
```

#### Quarterly

```bash
# Review GitHub Actions performance
# Update dependencies in requirements_static.txt

# Security audit of secrets-vault integration
# Rotate API keys and passwords

# Check ladder algorithm performance
# Adjust K_FACTOR if ratings are too volatile
```

#### Annually

```bash
# Full data backup and archive
# Create season summaries and player of year analysis

# Review and update DATA_MODEL.md
# Plan any schema changes for next season

# Evaluate if static architecture still meets needs
# Consider adding new features or integrations
```

## Contact and Support

- **Technical Issues**: Create GitHub issues in the repository
- **Questions about Ladder Rules**: Contact league administrator
- **Website Problems**: Check Vercel deployment logs
- **Data Corrections**: Update TOML files and run scripts

---

*This guide assumes you have appropriate permissions for the GitHub repository, Vercel account, and any external services like secrets-vault.*
---

## SOPS Integration (NEW)

### SOPS vs secrets-vault

**SOPS (Recommended)**:
- Mozilla's open-source secret management tool
- Age-based encryption (modern, secure, simple)
- Git-native encrypted files
- No external service dependencies
- Direct GitHub Actions integration

**secrets-vault (Alternative)**:
- External service for secret management
- Requires hosted vault server
- Additional dependency and complexity
- Centralized secret management

### Quick SOPS Setup

```bash
# Install SOPS and Age
wget https://github.com/mozilla/sops/releases/download/v3.8.1/sops-v3.8.1-linux.amd64
sudo mv sops-v3.8.1-linux.amd64 /usr/local/bin/sops
sudo chmod +x /usr/local/bin/sops

wget https://github.com/FiloSottile/age/releases/download/v1.1.1/age-v1.1.1-linux-amd64.tar.gz
tar -xvf age-v1.1.1-linux-amd64.tar.gz
sudo mv age/age /usr/local/bin/
sudo mv age/age-keygen /usr/local/bin/

# Generate age key
age-keygen -o age-key.txt
AGE_PUBLIC_KEY=$(cat age-key.txt | grep "public key" | cut -d' ' -f2)
AGE_PRIVATE_KEY=$(cat age-key.txt | grep "private key" | sed -n '2p' | cut -d' ' -f2)

# Add AGE_PRIVATE_KEY to GitHub Secrets
echo "Add this secret to GitHub: AGE_PRIVATE_KEY=$AGE_PRIVATE_KEY"

# Encrypt configuration
sops --encrypt --age $AGE_PUBLIC_KEY --output secrets/networth-secrets.toml.enc secrets/networth-secrets.toml

# Edit encrypted file (auto-encrypts on save)
sops secrets/networth-secrets.toml.enc
```

### Run SOPS Setup Workflow

Use GitHub Actions: **SOPS Secrets Setup** workflow to automatically:
- Install SOPS and Age
- Create encryption keys
- Generate encrypted template files
- Provide setup instructions

