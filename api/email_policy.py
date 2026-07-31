"""Shared safety policy for outbound email and protected automation actions."""

import os


VALID_DELIVERY_MODES = frozenset({'disabled', 'dry_run', 'live'})

CRON_PROTECTED_ACTIONS = frozenset({
    'send_availability_check',
    'send_availability_check_paused_only',
    'send_final_reminder',
    'send_midmonth_reminders',
    'resend_match_emails',
    'send_admin_alert',
    'check_recent_send',
    'reconcile_email_delivery',
    'test_auth_check',
})

DISABLED_PUBLIC_ACTIONS = frozenset({'send', 'send_welcome'})


def delivery_mode():
    """Return the configured delivery mode, failing closed for bad values."""
    value = os.environ.get('EMAIL_DELIVERY_MODE', 'disabled').strip().lower()
    return value if value in VALID_DELIVERY_MODES else 'disabled'


def is_live_delivery():
    return delivery_mode() == 'live'


def blocked_delivery_result(message_count, mode=None):
    """Describe a suppressed delivery without contacting the provider."""
    selected_mode = mode or delivery_mode()
    return {
        'success': True,
        'sent': 0,
        'failed': 0,
        'blocked': True,
        'would_send': message_count,
        'delivery_mode': selected_mode,
        'deliveries': [],
        'errors': [],
    }


def _authorization_value(handler):
    return handler.headers.get('Authorization', '').replace('Bearer ', '').strip()


def require_cron_secret(handler):
    """Authorize a workflow/admin request or write the appropriate response."""
    cron_secret = os.environ.get('CRON_SECRET', '').strip()
    if not cron_secret:
        handler._send_error(500, 'CRON_SECRET not configured')
        return False
    if _authorization_value(handler) != cron_secret:
        handler._send_error(401, 'Unauthorized')
        return False
    return True
