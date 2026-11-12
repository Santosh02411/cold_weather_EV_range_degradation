"""Scheduled Reports orchestration: check every enabled ReportSchedule
for whether it's due, generate + email the report (see
report_generation.py + report_email.py), and log the outcome to Report
History. Called by the periodic background job (see
services/scheduler.py) and also directly by a "send now" API action
for on-demand delivery without waiting for the schedule.
"""
from datetime import datetime

from ..models.report import ReportSchedule, ReportHistory
from ..models.user import User
from .. import db
from .report_generation import generate_report_bytes
from .report_email import send_report_email


def run_schedule(app_config, schedule):
    """Generate + email ONE schedule's report right now, log to Report
    History, and update last_sent_at -- regardless of whether the
    schedule was actually due (callers decide that; see
    run_due_report_schedules() below for the due-only periodic check,
    vs. an explicit "send now" button which should work anytime).
    """
    user = User.query.get(schedule.user_id)
    if not user:
        return None

    file_bytes, row_count, _ = generate_report_bytes(
        schedule.user_id, schedule.report_type, schedule.format,
        title=f"{schedule.report_type.title()} Report", subtitle=f"Scheduled report: {schedule.name}",
    )
    filename = f"{schedule.report_type}_{datetime.utcnow().strftime('%Y%m%d')}.{schedule.format}"
    sent, status = send_report_email(app_config, user, schedule.report_type, schedule.format, file_bytes, filename)

    history = ReportHistory(
        user_id=schedule.user_id, schedule_id=schedule.id, report_type=schedule.report_type,
        format=schedule.format, source='scheduled', row_count=row_count,
        delivered_via_email=sent, email_status=status,
    )
    db.session.add(history)
    schedule.last_sent_at = datetime.utcnow()
    db.session.commit()
    return history


def run_due_report_schedules(app):
    """Check every enabled schedule; run only the ones that are due.
    Called by the periodic scheduler job.
    """
    enabled = ReportSchedule.query.filter_by(enabled=True).all()
    due = [s for s in enabled if s.is_due()]
    results = {'checked': len(enabled), 'due': len(due), 'sent': 0, 'errors': 0}
    for schedule in due:
        try:
            history = run_schedule(app.config, schedule)
            if history and history.delivered_via_email:
                results['sent'] += 1
        except Exception as e:
            app.logger.error(f"[scheduled-reports] schedule {schedule.id} failed: {e}")
            results['errors'] += 1
    return results
