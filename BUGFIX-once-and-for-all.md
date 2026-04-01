# Net Worth Tennis: Email Automation Fix — Once and For All

## The Problem

Emails hadn't sent since March 4th. Every automated run either failed silently or was a no-op. Root cause: `CRON_SECRET` mismatch between GitHub Actions and Vercel Environment Variables — these are two separate systems.

## How CRON_SECRET Works

GitHub Actions stores it as a **Repository Secret**. Vercel stores it as an **Environment Variable**. They must have the **exact same value**. Changing one does not change the other. Both mask the value after saving — you cannot read it back.

## If You Ever Need to Reset CRON_SECRET

**You cannot copy secrets.** Both GitHub and Vercel mask stored values. You must generate a new one and set it in both places simultaneously:

```bash
# Step 1: Generate new secret
openssl rand -hex 32
```

1. Copy the generated value
2. **GitHub**: Settings → Secrets and variables → Actions → `CRON_SECRET` → Update
3. **Vercel**: Settings → Environment Variables → `CRON_SECRET` → paste same value → Production
4. **Vercel**: Redeploy (Deployments → latest → Redeploy)
5. Verify: Run `health_check` action in GitHub Actions

## Verification

After setting a new CRON_SECRET and redeploying:
1. GitHub Actions → biweekly-emails.yml → Run workflow → `health_check`
2. If auth test passes → you're good
3. If 401 → values don't match. Generate a new one and try again.

## Code Fixes (March 2026)

| File | Fix |
|------|-----|
| `api/email.py` | `test_auth_check` added to `PROTECTED_ACTIONS` — auth test now actually validates the secret |
| `api/join.py` | Rejects `.invalid`, `.test`, `.example` TLDs and test-looking emails at signup |
| `api/pairings.py` | Skips players with test email domains during pairing generation |

## Rules Going Forward

- **Never trigger email workflows manually.** Only scheduled runs.
- **Never test against production endpoints.** Use `.env` local values for testing.
- **GitHub Secrets and Vercel Env Vars are separate systems.** If a secret is needed by both, set it in both places at the same time.
- **You cannot read back a stored secret.** If you need to re-sync, generate a new one.
