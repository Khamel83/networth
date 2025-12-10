# Security Linter Fixes for NET WORTH Tennis

This document explains the Supabase security linter errors and how to fix them.

## Summary of Issues

Based on Supabase Database Linter results, we had:

### 🔴 ERROR Level (1 issue)
- **Security Definer View**: The `blocked_pairs` view was using `SECURITY DEFINER`, which enforces permissions of the view creator instead of the querying user

### ⚠️ WARN Level (5 issues)
- **Function Search Path Mutable**: 4 functions lacked `search_path` protection, making them vulnerable to search path injection attacks:
  - `update_player_rankings()`
  - `update_updated_at()`
  - `recalculate_rankings()`
  - `update_player_games()`
- **Auth Leaked Password Protection**: Password leak detection was disabled

## How to Fix

### 1. Database Fixes (SQL)

Run the migration file in Supabase SQL Editor:

```bash
# File: fix-security-linter-issues.sql
```

This will:
- ✅ Recreate `blocked_pairs` view without SECURITY DEFINER
- ✅ Add `SET search_path = ''` to all 4 functions with explicit schema qualification (`public.*`)
- ✅ Verify the changes were applied correctly

### 2. Auth Settings (Manual Configuration)

Enable leaked password protection in Supabase Dashboard:

1. Navigate to: **Authentication → Settings → Security & Protection**
2. Toggle ON: **"Leaked Password Protection"**
3. Save changes

This feature checks user passwords against the HaveIBeenPwned database to prevent use of compromised passwords.

## What Changed

### Before
```sql
CREATE OR REPLACE VIEW blocked_pairs AS ...;
-- No SECURITY DEFINER specified

CREATE OR REPLACE FUNCTION recalculate_rankings() ...;
-- No SET search_path
```

### After
```sql
CREATE VIEW blocked_pairs AS ...;
-- Explicitly created without SECURITY DEFINER

CREATE OR REPLACE FUNCTION recalculate_rankings()
...
SET search_path = ''  -- Prevents search path injection
AS $$
BEGIN
    -- All table references use explicit schema: public.players
    ...
END;
$$;
```

## Why These Changes Matter

### SECURITY DEFINER Risk
When a view has `SECURITY DEFINER`, it bypasses Row Level Security (RLS) policies and runs with the permissions of whoever created it. This can accidentally expose data that should be restricted.

### Search Path Injection Risk
Without `SET search_path`, an attacker could create a malicious table/function in their schema that shadows a legitimate one (e.g., create their own `players` table), causing the function to operate on the wrong objects.

By setting `search_path = ''` and explicitly qualifying all references (e.g., `public.players`), we ensure functions only operate on intended objects.

### Leaked Password Protection
Enabling this prevents users from choosing passwords that have been compromised in known data breaches, significantly improving account security.

## Verification

After running the migration, verify the fixes:

```sql
-- Check that blocked_pairs view works
SELECT COUNT(*) FROM blocked_pairs;

-- Verify functions are properly configured
SELECT routine_name, security_type
FROM information_schema.routines
WHERE routine_schema = 'public'
AND routine_name IN ('recalculate_rankings', 'update_player_games');

-- Test rankings still work
SELECT rank, name, total_games FROM players WHERE is_admin = false ORDER BY rank LIMIT 10;
```

All queries should execute successfully without errors.

## References

- [Supabase Database Linter - Security Definer View](https://supabase.com/docs/guides/database/database-linter?lint=0010_security_definer_view)
- [Supabase Database Linter - Function Search Path](https://supabase.com/docs/guides/database/database-linter?lint=0011_function_search_path_mutable)
- [Supabase Auth - Password Security](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection)
