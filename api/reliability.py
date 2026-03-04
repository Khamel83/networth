"""
Reliability helpers for scheduled automation.

These helpers are best-effort: if reliability tables are not migrated yet,
core API behavior still runs.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def preflight(required_env: Iterable[str], check_db: bool = True) -> Tuple[bool, Dict[str, Any]]:
    """
    Basic preflight checks for automation endpoints.
    Returns (ok, details) where details includes missing env vars and DB status.
    """
    missing = [name for name in required_env if not _env(name)]
    db_ok = True
    db_error = None

    if check_db:
        try:
            from api.supabase_http import table
            probe = table('players').select('id').limit(1).execute()
            db_ok = not bool(probe.error)
            db_error = probe.error
        except Exception as exc:  # pragma: no cover - defensive fallback
            db_ok = False
            db_error = str(exc)

    ok = not missing and db_ok
    return ok, {
        "missing_env": missing,
        "db_ok": db_ok,
        "db_error": db_error,
        "checked_at": _utc_now_iso(),
    }


def try_start_run(action: str, period_label: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Try to create an automation run record and acquire lock semantics.
    Returns (run_id, lock_error). If reliability tables are unavailable, run_id is None and lock_error is None.
    """
    try:
        from api.supabase_http import table

        # Lock rule: one running/succeeded run per action+period.
        existing = table('automation_runs')\
            .select('id, status')\
            .eq('action', action)\
            .eq('period_label', period_label)\
            .in_('status', ['running', 'succeeded'])\
            .order('started_at', desc=True)\
            .limit(1)\
            .execute()
        if existing.error:
            if _is_missing_table_error(existing.error):
                return None, None
            return None, f"Failed lock check: {existing.error}"
        if existing.data:
            status = existing.data[0].get('status')
            return None, f"Run already exists for {action} {period_label} (status={status})"

        created = table('automation_runs').insert({
            "action": action,
            "period_label": period_label,
            "status": "running",
            "started_at": _utc_now_iso(),
            "summary_json": metadata or {},
        }).execute()

        if created.error:
            if _is_missing_table_error(created.error):
                return None, None
            return None, f"Failed to start run: {created.error}"

        run_id = None
        if created.data:
            run_id = created.data[0].get('id')
        return run_id, None
    except Exception:
        # Reliability layer should never crash business logic.
        return None, None


def append_event(run_id: Optional[str], phase: str, severity: str, message: str, payload: Optional[Dict[str, Any]] = None) -> None:
    if not run_id:
        return
    try:
        from api.supabase_http import table
        result = table('automation_events').insert({
            "run_id": run_id,
            "event_type": phase,
            "severity": severity,
            "message": message,
            "payload_json": payload or {},
            "created_at": _utc_now_iso(),
        }).execute()
        if result.error and _is_missing_table_error(result.error):
            return
    except Exception:
        return


def update_run(run_id: Optional[str], status: str, summary: Optional[Dict[str, Any]] = None, error: Optional[Dict[str, Any]] = None) -> None:
    if not run_id:
        return
    try:
        from api.supabase_http import table
        payload: Dict[str, Any] = {
            "status": status,
            "ended_at": _utc_now_iso(),
        }
        if summary is not None:
            payload["summary_json"] = summary
        if error is not None:
            payload["error_json"] = error

        result = table('automation_runs').update(payload).eq('id', run_id).execute()
        if result.error and _is_missing_table_error(result.error):
            return
    except Exception:
        return


def _is_missing_table_error(error: Any) -> bool:
    text = str(error or "")
    lowered = text.lower()
    return (
        ("42P01" in text) or
        ("PGRST205" in text) or
        ("does not exist" in lowered) or
        ("could not find the table" in lowered) or
        ("relation" in lowered and "not found" in lowered)
    )


def _env(name: str) -> Optional[str]:
    import os
    value = os.environ.get(name)
    return value.strip() if isinstance(value, str) else value
