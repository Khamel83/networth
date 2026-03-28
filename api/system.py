"""
Vercel Serverless Function: System Utilities
Consolidated endpoint for health check and issue reporting.
Uses Supabase REST API (no Python supabase client).

Routes:
  GET  /api/system              → Health check
  POST /api/system              → Report issue (action: report_issue)
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime, timezone

# Initialize Sentry for error tracking
from api.sentry_init import init_sentry
from api.reliability import preflight, try_start_run, append_event, update_run
init_sentry()


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        """Health check endpoint"""
        db_status = "not_configured"
        supabase_available = False

        try:
            from api.supabase_http import table

            if os.environ.get('SUPABASE_URL') and os.environ.get('SUPABASE_ANON_KEY'):
                supabase_available = True
                try:
                    table('players').select('id').limit(1).execute()
                    db_status = "connected"
                except Exception:
                    db_status = "error"
        except Exception:
            db_status = "init_error"

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "healthy",
            "service": "networth-tennis",
            "version": "2.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": {
                "supabase_configured": bool(os.environ.get('SUPABASE_URL')),
                "supabase_available": supabase_available,
                "status": db_status
            },
            "environment": os.environ.get('VERCEL_ENV', 'development')
        }).encode())

    def do_POST(self):
        """Handle POST requests - currently only report_issue"""
        self._run_id = None
        self._run_action = None
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}

            action = data.get('action', 'report_issue')
            self._run_action = action

            if action == 'report_issue':
                self._handle_report_issue(data)
            elif action == 'reconcile_month':
                self._handle_reconcile_month(data)
            elif action == 'check_email_connectivity':
                self._handle_check_email_connectivity()
            elif action == 'unlock_stale_runs':
                self._handle_unlock_stale_runs(data)
            else:
                self._send_error(400, f"Unknown action: {action}")

        except Exception as e:
            self._send_error(500, str(e))

    def _handle_report_issue(self, data):
        """Handle issue report submission"""
        reporter_email = data.get('reporter_email', 'Anonymous')
        reporter_name = data.get('reporter_name', '')
        page_path = data.get('page_path', 'Unknown')
        message = data.get('message', '')

        if not message:
            self._send_error(400, "Missing 'message' field")
            return

        # Import email sender
        import resend

        api_key = os.environ.get('RESEND_API_KEY')
        if not api_key:
            self._send_error(500, "Email service not configured")
            return

        resend.api_key = api_key

        # Get sysadmin email only (other league admins don't need technical bug reports)
        admin_email = os.environ.get('ADMIN_EMAIL')
        if not admin_email:
            self._send_error(500, "ADMIN_EMAIL not configured")
            return

        # Build email
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .header h1 {{ color: #d165a4; margin: 0; }}
                .content {{ background: #f9f9f9; border-radius: 10px; padding: 30px; }}
                .field {{ margin-bottom: 20px; }}
                .field-label {{ font-weight: 600; color: #d165a4; }}
                .field-value {{ margin-top: 5px; }}
                .message {{ background: white; padding: 15px; border-radius: 5px; border-left: 3px solid #d165a4; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Issue Report</h1>
                </div>
                <div class="content">
                    <div class="field">
                        <div class="field-label">From:</div>
                        <div class="field-value">{reporter_name} ({reporter_email})</div>
                    </div>
                    <div class="field">
                        <div class="field-label">Page:</div>
                        <div class="field-value">{page_path}</div>
                    </div>
                    <div class="field">
                        <div class="field-label">Time:</div>
                        <div class="field-value">{timestamp}</div>
                    </div>
                    <div class="field">
                        <div class="field-label">Message:</div>
                        <div class="message">{message}</div>
                    </div>
                </div>
                <div class="footer">
                    <p>Net Worth Tennis - User Report</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Send email to sysadmin
        params = {
            "from": "Net Worth Tennis <hello@networthtennis.com>",
            "to": admin_email,
            "subject": f"Issue Report from {reporter_name or 'User'}",
            "html": html,
            "reply_to": reporter_email if reporter_email != 'Anonymous' else 'ashleybrooke.kaufman@gmail.com'
        }

        response = resend.Emails.send(params)

        self._send_success({
            "message": "Issue report sent to sysadmin",
            "id": response.get('id')
        })

    def _handle_reconcile_month(self, data):
        """Reconcile known data drift for a given month."""
        from api.supabase_http import table

        cron_secret = os.environ.get('CRON_SECRET', '')
        if not cron_secret:
            self._send_error(500, "CRON_SECRET not configured")
            return
        auth = self.headers.get('Authorization', '').replace('Bearer ', '')
        if auth != cron_secret and '@' not in auth:
            self._send_error(401, "Unauthorized")
            return

        period_label = data.get('period_label', datetime.now().strftime('%B %Y'))
        dry_run = bool(data.get('dry_run', False))

        run_id, lock_error = try_start_run('reconcile_month', period_label, {
            'source': 'api/system',
            'dry_run': dry_run,
        })
        self._run_id = run_id
        if lock_error:
            self._send_error(409, lock_error)
            return

        ok, details = preflight(
            required_env=['SUPABASE_URL', 'SUPABASE_ANON_KEY'],
            check_db=True
        )
        if not ok:
            append_event(run_id, 'preflight', 'error', 'Preflight failed', details)
            self._send_error(500, f"Preflight failed: {details}")
            return

        append_event(run_id, 'preflight', 'info', 'Preflight passed', details)

        repairs = []
        issues = []

        matches_result = table('matches').select('id, assignment_id, player1_id, player2_id, period_label').eq('period_label', period_label).execute()
        if matches_result.error:
            self._send_error(500, f"Failed to load matches: {matches_result.error}")
            return

        assignments_result = table('match_assignments').select('id, player1_id, player2_id, period_label, status, match_id').eq('period_label', period_label).execute()
        if assignments_result.error:
            self._send_error(500, f"Failed to load assignments: {assignments_result.error}")
            return

        assignments = assignments_result.data or []
        assignment_by_id = {a.get('id'): a for a in assignments}
        assignment_by_pair = {}
        for a in assignments:
            key = frozenset([a.get('player1_id'), a.get('player2_id')])
            assignment_by_pair[key] = a

        for m in matches_result.data or []:
            assignment = None
            assignment_id = m.get('assignment_id')
            if assignment_id:
                assignment = assignment_by_id.get(assignment_id)
            if not assignment:
                key = frozenset([m.get('player1_id'), m.get('player2_id')])
                assignment = assignment_by_pair.get(key)

            if not assignment:
                issues.append({
                    'match_id': m.get('id'),
                    'issue': 'no_matching_assignment',
                })
                continue

            needs_status = assignment.get('status') != 'completed'
            needs_match = assignment.get('match_id') != m.get('id')
            if not needs_status and not needs_match:
                continue

            update_payload = {}
            if needs_status:
                update_payload['status'] = 'completed'
            if needs_match:
                update_payload['match_id'] = m.get('id')

            if not dry_run:
                update_result = table('match_assignments').update(update_payload).eq('id', assignment.get('id')).execute()
                if update_result.error:
                    issues.append({
                        'assignment_id': assignment.get('id'),
                        'issue': f"update_failed: {update_result.error}",
                    })
                    continue

            repairs.append({
                'assignment_id': assignment.get('id'),
                'match_id': m.get('id'),
                'changes': update_payload,
            })

        status = 'succeeded' if not issues else 'failed_terminal'
        summary = {
            'period_label': period_label,
            'dry_run': dry_run,
            'repairs_applied': len(repairs),
            'remaining_issues': len(issues),
        }
        if issues:
            append_event(run_id, 'reconcile', 'warning', 'Reconcile completed with issues', {
                'issues': issues[:20],
                'repairs_preview': repairs[:20],
            })
        else:
            append_event(run_id, 'reconcile', 'info', 'Reconcile completed cleanly', summary)

        update_run(run_id, status, summary=summary, error={'issues': issues} if issues else None)
        if issues:
            self._send_error(500, f"Reconcile completed with {len(issues)} unresolved issue(s)")
            return
        self._send_success({
            'period_label': period_label,
            'dry_run': dry_run,
            'repairs_applied': repairs,
            'remaining_issues': issues,
            'status': status,
        })

    def _handle_check_email_connectivity(self):
        """Validate Resend API key by making a read-only API call"""
        import resend

        api_key = os.environ.get('RESEND_API_KEY')
        if not api_key:
            self._send_error(500, "RESEND_API_KEY not configured")
            return

        resend.api_key = api_key
        try:
            resend.ApiKeys.list()
            self._send_success({"email_service": "connected", "provider": "resend"})
        except resend.exceptions.AuthenticationError as e:
            self._send_error(500, f"Resend authentication failed: {str(e)}")
        except Exception as e:
            self._send_error(500, f"Resend connectivity check failed: {str(e)}")

    def _handle_unlock_stale_runs(self, data):
        """Mark stale 'running' automation_runs as failed so locks can be retried."""
        from api.supabase_http import table

        cron_secret = os.environ.get('CRON_SECRET', '')
        if not cron_secret:
            self._send_error(500, "CRON_SECRET not configured")
            return
        auth = self.headers.get('Authorization', '').replace('Bearer ', '')
        if auth != cron_secret:
            self._send_error(401, "Unauthorized")
            return

        action_filter = data.get('action')  # optional: only unlock a specific action
        period_filter = data.get('period_label')  # optional: only a specific period

        q = table('automation_runs').select('id, action, period_label, started_at').in_('status', ['running'])
        if action_filter:
            q = q.eq('action', action_filter)
        if period_filter:
            q = q.eq('period_label', period_filter)

        result = q.execute()
        if result.error:
            self._send_error(500, f"Failed to query stale runs: {result.error}")
            return

        unlocked = []
        for row in (result.data or []):
            upd = table('automation_runs').update({
                'status': 'failed_terminal',
                'ended_at': datetime.now(timezone.utc).isoformat(),
                'error_json': {'reason': 'manually unlocked via admin action'},
            }).eq('id', row['id']).execute()
            if not upd.error:
                unlocked.append({'id': row['id'], 'action': row['action'], 'period_label': row['period_label']})

        self._send_success({'unlocked': unlocked, 'count': len(unlocked)})

    def _send_success(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        payload = {"success": True, **data}
        run_id = getattr(self, '_run_id', None)
        if run_id:
            payload['run_id'] = run_id
        self.wfile.write(json.dumps(payload).encode())

    def _send_error(self, status, message):
        run_id = getattr(self, '_run_id', None)
        if run_id:
            append_event(run_id, 'error', 'error', message, {'status': status, 'action': getattr(self, '_run_action', None)})
            update_run(run_id, 'failed_terminal', error={'status': status, 'message': message})
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        payload = {"success": False, "error": message}
        if run_id:
            payload['run_id'] = run_id
        self.wfile.write(json.dumps(payload).encode())
