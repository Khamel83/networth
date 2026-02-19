"""
Sentry initialization for error tracking
Import this at the top of any API file that needs error reporting
"""
import os

_initialized = False

def init_sentry():
    """Initialize Sentry if DSN is configured"""
    global _initialized
    if _initialized:
        return

    dsn = os.environ.get('SENTRY_DSN')
    if not dsn:
        return

    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=dsn,
            send_default_pii=True,
            traces_sample_rate=0.1,  # 10% sampling to stay within free tier
        )
        _initialized = True
    except ImportError:
        # Sentry SDK not installed (e.g., in test environment)
        pass

# Auto-initialize when imported
init_sentry()
