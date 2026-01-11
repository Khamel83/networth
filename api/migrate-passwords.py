"""
One-time migration: Set initial passwords for all players
Password = 10-digit phone number OR tennis123
"""
import os
import json
import bcrypt
from supabase import create_client


def handler(event, context):
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_ANON_KEY')

    if not supabase_url or not supabase_key:
        return {"statusCode": 500, "body": "Supabase credentials missing"}

    supabase = create_client(supabase_url, supabase_key)

    players = supabase.table('players').select('id, email, phone').execute()

    results = {"updated": 0, "skipped": 0, "errors": []}

    for player in players.data:
        try:
            if player.get('password_hash'):
                results["skipped"] += 1
                continue

            phone = player.get('phone', '')

            if phone:
                # Strip to 10 digits only
                digits = ''.join(c for c in phone if c.isdigit())
                if len(digits) > 10:
                    digits = digits[-10:]
                password = digits
            else:
                password = 'tennis123'

            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

            supabase.table('players').update({
                'password_hash': hashed,
                'password_changed': False
            }).eq('id', player['id']).execute()

            results["updated"] += 1

        except Exception as e:
            results["errors"].append(f"{player.get('email', 'unknown')}: {str(e)}")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(results, indent=2)
    }
