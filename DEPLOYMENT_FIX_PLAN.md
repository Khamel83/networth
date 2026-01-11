# Fix Vercel 250MB Deployment Issue

## The Problem

- Vercel limit: 250MB per function
- Current error: "Serverless Function has exceeded the unzipped maximum size of 250 MB"
- Deploy time: 4.5+ minutes (way too long)

## Root Cause

The `supabase` Python package pulls in `pyiceberg` which is 100+ MB.
We don't need it - we only use basic database queries (select, insert, update).

## The Solution

Replace the `supabase` Python client with **raw HTTP calls** to Supabase's REST API.

This eliminates the heavy dependency entirely.

---

## Files to Change

1. **api/auth.py** - Replace supabase client with HTTP calls
2. **api/join.py** - Replace supabase client with HTTP calls
3. **api/players.py** - Replace supabase client with HTTP calls
4. **api/pairings.py** - Replace supabase client with HTTP calls
5. **api/profile.py** - Replace supabase client with HTTP calls
6. **api/admin.py** - Replace supabase client with HTTP calls
7. **api/matches.py** - Replace supabase client with HTTP calls
8. **api/migrate-passwords.py** - Replace supabase client with HTTP calls
9. **api/upload.py** - Replace supabase client with HTTP calls
10. **requirements.txt** - Remove `supabase`, keep only `httpx` and `resend`

---

## Implementation Pattern

### Before (using supabase package):
```python
from supabase import create_client
supabase = create_client(url, key)
result = supabase.table('players').select('*').execute()
```

### After (using HTTP):
```python
import httpx

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY')

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}'
}

# SELECT
response = httpx.get(f'{SUPABASE_URL}/rest/v1/players', headers=headers)
data = response.json()

# INSERT
response = httpx.post(
    f'{SUPABASE_URL}/rest/v1/players',
    headers=headers,
    json={'email': 'test@test.com', 'name': 'Test'}
)

# UPDATE
response = httpx.patch(
    f'{SUPABASE_URL}/rest/v1/players?id=eq.123',
    headers=headers,
    json={'name': 'Updated'}
)
```

---

## Step-by-Step Plan

### Step 1: Create a shared HTTP helper
**File:** `api/supabase_http.py` (NEW)

This file will have helper functions for all database operations so we don't repeat code.

### Step 2: Update each API file
Replace `get_supabase_client()` with HTTP calls using the helper.

### Step 3: Update requirements.txt
Remove `supabase`, keep only:
- `httpx>=0.24.0`
- `resend>=0.5.0`

### Step 4: Test locally
Verify the API endpoints still work.

### Step 5: Deploy to Vercel
Should be much faster and under 250MB.

---

## Expected Result

- **Bundle size:** ~10-20 MB (down from 250MB+)
- **Deploy time:** ~30 seconds (down from 4.5+ minutes)
- **Functionality:** Exactly the same

---

## Risk Assessment

**Risk:** Breaking existing database queries

**Mitigation:**
1. Create helper functions that match the old supabase API exactly
2. Test each endpoint before deploying
3. Can roll back by reverting the commit

---

## Why This Will Work

1. **Supabase REST API** is what the Python client uses under the hood anyway
2. **httpx** is small (~1MB) and already in requirements.txt
3. **No pyiceberg** - we only use the REST API, not storage
4. We only use basic CRUD operations - no complex queries

---

## Validation Checklist

After implementing, verify:

- [ ] auth.py: Login works
- [ ] join.py: Signup works
- [ ] players.py: Player list loads
- [ ] profile.py: Profile loads and saves
- [ ] All files compile without errors
- [ ] requirements.txt has only httpx and resend
- [ ] Local testing passes
