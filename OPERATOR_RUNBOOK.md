# NET WORTH Static System - Operator Runbook

## 🎯 Overview

This runbook provides step-by-step instructions for deploying and operating the NET WORTH static tennis ladder system.

**Architecture**: Static site + GitHub Actions + TOML data + Vercel
**Prerequisites**: Git, Python 3.11+, GitHub account, Vercel account
**Time to deploy**: 30-45 minutes
**Maintenance**: Minimal (weekly automated updates)

---

## 🚀 Initial Deployment Setup

### Step 1: Repository Preparation

```bash
# Clone the repository
git clone https://github.com/Khamel83/networth.git
cd networth

# Install Python TOML processing libraries
pip install tomli-w tomli

# Make scripts executable
chmod +x scripts/*.py

# Create data and public directories
mkdir -p data public
```

### Step 2: Data Bootstrap (if migrating from existing database)

```bash
# If you have networth_tennis.db from legacy system:
python scripts/bootstrap_from_sqlite.py --db networth_tennis.db --force

# This creates:
# - data/players.toml (16 players imported)
# - data/matches.toml (empty initially)
```

### Step 3: Initial Ladder and Pairings Generation

```bash
# Compute ladder rankings
python scripts/recompute_ladder.py --verbose

# Generate weekly pairings
python scripts/generate_pairings.py --verbose

# Export static JSON for frontend
python scripts/export_static_json.py --verbose

# Verify outputs:
ls -la data/          # Should have .toml files
ls -la public/          # Should have .json files
```

### Step 4: Local Testing

```bash
# Test locally before deployment
python3 -m http.server 8080

# In another terminal:
curl http://localhost:8080/ladder.json | head -n 5
curl http://localhost:8080/pairings.json | head -n 5
curl http://localhost:8080/players.json | head -n 5

# Open browser:
# Visit http://localhost:8080
# Check ladder loads correctly (no "Loading..." message)
# Verify JSON loads via browser console (F12 → Network)
```

### Step 5: Deploy to Vercel

#### 5.1 Connect Repository to Vercel

1. **Sign in**: Go to [vercel.com](https://vercel.com) and sign in
2. **New Project**: Click "New Project"
3. **Import Git**: Choose "Import Git Repository"
4. **Select Repo**: Choose `Khamel83/networth` from list
5. **Configure**: Vercel auto-detects static site
6. **Deploy**: Click "Deploy"

#### 5.2 Configure Custom Domain

1. **Domain Settings**: In Vercel dashboard → "Domains"
2. **Add Domain**: Enter `networthtennis.com`
3. **DNS Configuration**: Vercel provides DNS records
4. **Update DNS**: At your domain registrar:
   ```
   Type: CNAME
   Name: @
   Value: cname.vercel-dns.com
   TTL: 300
   ```

5. **SSL**: Vercel automatically provisions SSL certificate

### Step 6: Setup SOPS for Secret Management

#### 6.1 Install SOPS Locally

```bash
# Install SOPS
wget https://github.com/mozilla/sops/releases/download/v3.8.1/sops-v3.8.1-linux.amd64
sudo mv sops-v3.8.1-linux.amd64 /usr/local/bin/sops
sudo chmod +x /usr/local/bin/sops

# Install Age encryption
wget https://github.com/FiloSottile/age/releases/download/v1.1.1/age-v1.1.1-linux-amd64.tar.gz
tar -xvf age-v1.1.1-linux-amd64.tar.gz
sudo mv age/age /usr/local/bin/
sudo mv age/age-keygen /usr/local/bin/

# Generate encryption keys
age-keygen -o age-key.txt
AGE_PUBLIC_KEY=$(cat age-key.txt | grep "public key" | cut -d' ' -f2)
AGE_PRIVATE_KEY=$(cat age-key.txt | grep "private key" | sed -n '2p' | cut -d' ' -f2)
```

#### 6.2 Add GitHub Secrets

In GitHub → Settings → Secrets and variables → Actions:

```
AGE_PRIVATE_KEY: [paste from age-key.txt]
```

#### 6.3 Run SOPS Setup Workflow

```bash
# Go to GitHub Actions → SOPS Secrets Setup
# Click "Run workflow"
# This creates encrypted template files and setup instructions
```

### Step 7: Configure GitHub Actions

#### 7.1 Enable Automatic Updates

The `.github/workflows/networth_static_pipeline.yml` automatically:
- **Runs weekly**: Every Monday 1:00 UTC (Sunday 6:00 PM PT)
- **Runs on push**: When data files change
- **Runs manually**: Via GitHub Actions UI

#### 7.2 Verify Workflow Permissions

In GitHub repository → Settings → Actions → General:

```bash
✅ Allow "Actions" to run
✅ Allow "GITHUB_TOKEN" to push changes
✅ Contents: Read and write
```

#### 7.3 Test Weekly Pipeline

```bash
# Manually trigger workflow:
# GitHub → Actions → NET WORTH Static Pipeline → "Run workflow"

# Monitor execution:
# Check Actions tab for progress
# Verify commits appear in repository
```

---

## 📋 Regular Operations

### Daily Tasks

```bash
# Check for any urgent ladder issues
git log --oneline -5 --grep="ladder"

# Monitor player feedback emails
# Check matches@networthtennis.com for new match reports
```

### Weekly Tasks (Automated)

The GitHub Actions workflow automatically handles:

1. **Monday 1:00 UTC**:
   ```bash
   python scripts/recompute_ladder.py      # Update rankings
   python scripts/generate_pairings.py      # New weekly matches
   python scripts/export_static_json.py     # Update frontend data
   # Commits changes back to repository
   ```

2. **Manual Trigger** (if needed):
   ```bash
   # GitHub Actions → NET WORTH Static Pipeline → "Run workflow"
   ```

### Monthly Tasks

```bash
# Review ladder algorithm performance
git log --oneline --since="1 month ago" --grep="recompute"

# Backup data directory
cp -r data/ data_backup_$(date +%Y%m)/

# Review SOPS key rotation (every 90 days)
age-keygen -o age-key-$(date +%Y%m).txt

# Archive old match history
# Keep last 6 months detailed, older as summaries
```

---

## 🔧 Common Operations

### Adding New Players

```bash
# 1. Add to data/players.toml:
[[players]]
id = "new_player_$(date +%s)"
name = "New Player Name"
email = "player@email.com"
active = true
initial_rating = 1500
preferred_courts = ["vermont_canyon", "griffith_riverside"]

[players.availability]
mon_evening = true
wed_evening = true
fri_evening = true
sun_evening = true

# 2. Regenerate ladder:
python scripts/recompute_ladder.py --verbose

# 3. Generate new pairings:
python scripts/generate_pairings.py --verbose

# 4. Export for frontend:
python scripts/export_static_json.py --verbose

# 5. Commit changes:
git add data/ public/
git commit -m "Add new player: New Player Name

🤖 Generated with Claude Code"
git push
```

### Recording Match Results

```bash
# 1. Add to data/matches.toml:
[[matches]]
id = "2025-03-15-player1-player2"
date = "2025-03-15"
player1_id = "player1_id"
player2_id = "player2_id"
court_id = "vermont_canyon"
scoreline = "6-4 6-2"
winner_id = "player1_id"
had_fun_player1 = true
had_fun_player2 = true
source = "manual"

# 2. Recompute ladder:
python scripts/recompute_ladder.py --verbose

# 3. Update pairings for remaining players:
python scripts/generate_pairings.py --verbose

# 4. Export JSON:
python scripts/export_static_json.py --verbose

# 5. Commit:
git add data/ public/
git commit -m "Add match: Player1 vs Player2 (Mar 15)

🤖 Generated with Claude Code"
git push
```

### Updating Player Availability

```bash
# 1. Edit data/players.toml to update availability:
[players.availability]
mon_evening = true
tue_evening = false
wed_evening = true
# ... update as needed

# 2. Regenerate pairings:
python scripts/generate_pairings.py --verbose

# 3. Export JSON:
python scripts/export_static_json.py --verbose

# 4. Commit:
git add data/ public/
git commit -m "Update availability: Player Name

🤖 Generated with Claude Code"
git push
```

---

## 🔍 Troubleshooting

### Ladder Not Loading on Website

**Check JSON endpoints**:
```bash
curl -I https://networthtennis.com/ladder.json
# Should return 200 OK

curl -s https://networthtennis.com/ladder.json | jq '.metadata'
# Should show valid JSON structure
```

**Check GitHub Actions**:
```bash
# GitHub → Actions → NET WORTH Static Pipeline
# Look for errors in workflow logs
```

**Check Data Files**:
```bash
# Verify TOML files exist and are valid:
python -c "
import tomllib
with open('data/ladder_snapshot.toml', 'rb') as f:
    data = tomllib.load(f)
    print(f'Ladder has {len(data.get(\"ladder\", []))} players')
"
```

### GitHub Actions Failures

**Common Issues**:

1. **Permission Denied**:
   ```bash
   # Repository → Settings → Actions → General
   # Enable: Allow Actions + GITHUB_TOKEN write access
   ```

2. **Missing Dependencies**:
   ```bash
   # Check .github/workflows/networth_static_pipeline.yml
   # Ensure Python 3.11+ specified
   ```

3. **SOPS Decryption Errors**:
   ```bash
   # Verify AGE_PRIVATE_KEY secret exists
   # Check key format (no extra spaces/newlines)
   ```

### Email Notification Issues

**For SOPS integration**:
```bash
# Check encrypted email configuration:
sops secrets/networth-secrets.toml.enc

# Verify SOPS workflow completed successfully
# Check GitHub Actions logs for setup-secrets job
```

**For secrets-vault integration**:
```bash
# Test vault access:
export VAULT_TOKEN="your_token"
export VAULT_ADDR="https://your-vault-server"
vault read secret/networth/email
```

---

## 📊 Monitoring and Analytics

### Website Monitoring

```bash
# Check Vercel Analytics Dashboard
# Visit: vercel.com/your-project/analytics

# Monitor:
# - Page load times
# - Error rates
# - Geographic distribution
# - Device/breakdown
```

### Ladder Health Metrics

```bash
# Weekly health check via GitHub Actions schedule
# Automates: recompute → generate → export → commit

# Manual health check:
git log --oneline --since="1 week ago" --grep="ladder"
# Should show successful weekly updates
```

### Player Engagement Tracking

```bash
# Track participation metrics:
git log --oneline --since="1 month ago" --grep="Add match" | wc -l
# Count of matches recorded per month

# Monitor active players:
python -c "
import tomllib
with open('data/players.toml', 'rb') as f:
    data = tomllib.load(f)
    active = [p for p in data.get('players', []) if p.get('active', False)]
    print(f'Active players: {len(active)}/{len(data.get(\"players\", []))}')
"
```

---

## 🚨 Emergency Procedures

### Data Corruption Recovery

```bash
# 1. Check git history:
git log --oneline -10 data/

# 2. Restore from last known good state:
git checkout HEAD~1 -- data/ ladder_snapshot.toml

# 3. Re-run pipeline:
python scripts/recompute_ladder.py
python scripts/export_static_json.py

# 4. Verify and commit:
git add data/ public/
git commit -m "Emergency ladder recovery

🤖 Generated with Claude Code"
```

### Website Down

```bash
# 1. Check Vercel status:
https://vercel-status.com/

# 2. Check deployment:
vercel --prod --yes

# 3. Redeploy if needed:
git push origin main
```

### Security Incident

```bash
# 1. Rotate SOPS keys:
age-keygen -o age-key-$(date +%Y%m%d%H%M).txt

# 2. Update GitHub Secrets:
# Replace AGE_PRIVATE_KEY with new key

# 3. Re-encrypt sensitive files:
for file in secrets/*.enc; do
    sops --decrypt $file > temp.toml
    sops --encrypt --age $NEW_PUBLIC_KEY --output $file temp.toml
    rm temp.toml
done

# 4. Update all team members' keys
# Distribute new public key for encryption
```

---

## 📞 Contact and Support

- **Technical Issues**: Create GitHub issues in repository
- **Ladder Questions**: Contact league administrator
- **SOPS/Secrets Issues**: Review SOPS documentation and workflow logs
- **Vercel Issues**: Check Vercel status page and support
- **Email Problems**: Verify SMTP configuration in secrets

---

## ✅ Success Criteria

Your NET WORTH static system is working when:

- [ ] Website loads at networthtennis.com
- [ ] Ladder displays current rankings from JSON
- [ ] Pairings show weekly suggested matches
- [ ] GitHub Actions run weekly without errors
- [ ] SOPS encryption/decryption works locally
- [ ] Data changes trigger automatic updates
- [ ] JSON files are accessible via HTTP
- [ ] SSL certificate is valid and green padlock shows
- [ ] Mobile responsive design works on phones
- [ ] Player additions trigger ladder updates

---

**🎉 Congratulations!** Your NET WORTH tennis ladder is now running as a modern, static system with automated updates and secure secret management.

*Last updated: November 2025*