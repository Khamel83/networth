"""
Sentry initialization for error tracking
Import this at the top of any API file that needs error reporting
"""
import os
import sentry_sdk

_initialized = False

def init_sentry():
    """Initialize Sentry if DSN is configured"""
    global _initialized
    if _initialized:
        return

    dsn = os.environ.get('SENTRY_DSN')
    if dsn:
        sentry_sdk.init(
            dsn=dsn,
            send_default_pii=True,
            traces_sample_rate=1.0,  # 100% for now to verify it's working
        )
        _initialized = True

        # Send a test message to confirm Sentry is working
        sentry_sdk.capture_message("Sentry initialized - test message from Net Worth Tennis")

# Auto-initialize when imported
init_sentry()
