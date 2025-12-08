# Player Profile Feature - Implementation Guide

## Overview

Added comprehensive player profile functionality to NET WORTH Tennis ladder system, including:
- Profile pictures
- Neighborhood location
- Instagram handles
- Fun facts (favorite tennis player or match)

## Changes Made

### 1. Database Schema (`migration-add-profiles.sql`)

Added 4 new columns to the `players` table:
```sql
- profile_picture TEXT    -- URL to profile image
- neighborhood TEXT       -- Player's neighborhood (e.g., "Silver Lake")
- instagram_handle TEXT   -- Instagram username (without @)
- fun_fact TEXT          -- Favorite player or tennis match watched
```

**To apply this migration:**
```bash
# Run migration-add-profiles.sql in Supabase SQL Editor
```

The migration also includes sample data for the top 10 players using placeholder avatar images from pravatar.cc.

### 2. API Updates

#### `api/profile.py`
- **GET endpoint**: Now returns profile fields in addition to existing data
- **POST endpoint**: Accepts profile field updates via the `action: 'update'` parameter

Example request:
```json
{
  "action": "update",
  "profile_picture": "https://example.com/photo.jpg",
  "neighborhood": "Echo Park",
  "instagram_handle": "mytennis",
  "fun_fact": "Favorite player: Serena Williams"
}
```

#### `api/players.py`
- Updated `SAMPLE_PLAYERS` fallback data to include profile fields
- Supabase queries automatically return new profile fields

#### `api/email.py`
- Updated `get_pairing_email_html()` to accept and display opponent profile info
- Email templates now show:
  - Profile photo (or initials if no photo)
  - Neighborhood with location pin emoji
  - Instagram handle with camera emoji
  - Fun fact in highlighted card

#### `api/cron/monthly.py`
- Monthly pairing emails now pass opponent profile data
- Players receive rich profile cards of their matched opponents

### 3. UI Updates (`public/index.html`)

#### Ladder Display
- Added "Photo" column to the ladder table
- Shows circular profile photos (or initials if no photo)
- Displays neighborhood below skill level in gold color
- Rows are now clickable to view full profiles

#### Profile Modal
- Click any player row to view detailed profile
- Shows:
  - Large profile photo
  - Rank badge
  - Stats (games won, matches played)
  - Neighborhood
  - Instagram link (clickable)
  - Fun fact in styled card
- Close modal with:
  - × button
  - Escape key
  - Click outside modal

### 4. Responsive Design

Mobile-friendly adjustments:
- Profile photos scale appropriately
- Modal adapts to small screens
- Grid columns hide/show based on viewport

## Usage

### For Players

**Update your profile:**
1. Log in to networthtennis.com
2. Go to Dashboard
3. Click "Edit Profile"
4. Add/update:
   - Profile photo URL
   - Your neighborhood
   - Instagram handle
   - Your favorite tennis player or match

**View other players:**
- Click any row on the public ladder
- See their profile, location, Instagram, and tennis fandom

### For Admins

**Add profile data directly in Supabase:**
```sql
UPDATE players SET
  profile_picture = 'https://...',
  neighborhood = 'Silver Lake',
  instagram_handle = 'username',
  fun_fact = 'Favorite match: 2019 Wimbledon Final'
WHERE email = 'player@example.com';
```

**Batch update via CSV import:**
- Export players table
- Add profile columns
- Re-import to Supabase

## Sample Data

Migration includes fake profile data for top 10 players:
- Profile pictures from pravatar.cc (placeholder avatars)
- Diverse East LA neighborhoods
- Sample Instagram handles
- Variety of favorite players (Serena, Venus, Naomi, Coco, etc.)

**To update with real data:**
- Replace pravatar.cc URLs with actual player photos
- Update neighborhoods based on player location
- Collect real Instagram handles
- Ask players for their tennis fan moments

## Testing

1. **Database migration:**
   ```sql
   -- Verify columns exist
   SELECT column_name FROM information_schema.columns
   WHERE table_name = 'players'
   AND column_name IN ('profile_picture', 'neighborhood', 'instagram_handle', 'fun_fact');
   ```

2. **API testing:**
   ```bash
   # Test player list includes profiles
   curl https://networthtennis.com/api/players

   # Test profile update (requires auth)
   curl -X POST https://networthtennis.com/api/profile \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"action":"update","neighborhood":"Echo Park"}'
   ```

3. **UI testing:**
   - Visit networthtennis.com
   - Verify photos appear in ladder
   - Click player row to see modal
   - Check mobile responsiveness

4. **Email testing:**
   - Trigger test pairing email
   - Verify opponent profile displays
   - Check that photos, neighborhood, Instagram, and fun facts appear

## Deployment Checklist

- [x] Run migration SQL in Supabase
- [ ] Test API endpoints in production
- [ ] Verify UI on live site
- [ ] Send test pairing email
- [ ] Update CLAUDE.md with profile info
- [ ] Notify players about new feature

## Future Enhancements

- File upload for profile pictures (instead of URLs)
- Auto-fetch Instagram profile pics via API
- Map view showing player neighborhoods
- Filter ladder by neighborhood
- "Tennis style" field (aggressive, defensive, etc.)
- Availability calendar integration
- Match history with specific opponents in profile

## Files Changed

```
migration-add-profiles.sql          # NEW - Database migration
api/profile.py                      # MODIFIED - Added profile fields
api/players.py                      # MODIFIED - Updated sample data
api/email.py                        # MODIFIED - Profile in emails
api/cron/monthly.py                 # MODIFIED - Pass profile to emails
public/index.html                   # MODIFIED - UI with profiles & modal
```

## Support

Questions? Check:
- [CLAUDE.md](/CLAUDE.md) - Main project docs
- [Supabase Dashboard](https://supabase.com) - Database management
- [Vercel Dashboard](https://vercel.com) - Deployment logs
