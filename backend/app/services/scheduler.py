"""
FEAT-3: periodic background scheduler for cold-snap alert checks, using
APScheduler's BackgroundScheduler (runs in-process, no separate worker
service needed -- appropriate for this project's single-process
deployment target; a real production deployment with multiple workers
would need this moved to a proper task queue like Celery so the job
doesn't run once per worker process, noted as a real limitation rather
than glossed over).

Guards against Flask's debug reloader starting the scheduler twice (it
forks a child process and re-runs the whole app factory in it) using
the same WERKZEUG_RUN_MAIN check Flask's own docs recommend for this
exact problem.
"""
import os


def init_scheduler(app):
    if not app.config.get('ALERTS_ENABLED', True):
        app.logger.info("ALERTS_ENABLED=false -- cold-snap alert scheduler not started.")
        return None

    # In Flask's debug reloader, the app factory runs once in the
    # reloader parent process and once in the actual worker child --
    # starting the scheduler in both would run every check twice.
    # WERKZEUG_RUN_MAIN is only set in the child, so skip the parent.
    if app.config.get('DEBUG') and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        return None

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        app.logger.warning(
            "APScheduler not installed -- cold-snap alerts won't run on a "
            "schedule. Install it (see requirements.txt) to enable FEAT-3."
        )
        return None

    from .alerts import check_and_send_alerts

    scheduler = BackgroundScheduler(daemon=True)

    def _job():
        with app.app_context():
            try:
                results = check_and_send_alerts(app)
                app.logger.info(f"[alerts] checked={results['checked']} "
                                 f"triggered={results['triggered']} sent={results['sent']} "
                                 f"skipped_cooldown={results['skipped_cooldown']} errors={results['errors']}")
            except Exception as e:
                app.logger.error(f"[alerts] scheduled check failed: {e}")

    interval = app.config.get('ALERT_CHECK_INTERVAL_MINUTES', 60)
    # Default 'interval' trigger behavior already waits one full interval
    # before the first run (not immediately on boot) -- no extra
    # next_run_time argument needed. (A first pass at this incorrectly
    # passed next_run_time=None, which in APScheduler actually means
    # "don't auto-schedule a run at all" -- caught before this shipped;
    # see docs/PROJECT_WORKFLOW.md.)
    scheduler.add_job(_job, 'interval', minutes=interval, id='cold_snap_alerts')

    _add_live_retrain_job(app, scheduler)
    _add_scheduled_reports_job(app, scheduler)
    _add_notification_jobs(app, scheduler)

    scheduler.start()
    app.logger.info(f"[alerts] scheduler started, checking every {interval} minute(s).")
    return scheduler


def _add_live_retrain_job(app, scheduler):
    """Live Model Retraining: periodic data-drift check, gated by
    LIVE_RETRAIN_ENABLED same as the alerts job above is gated by
    ALERTS_ENABLED. This only controls whether the periodic CHECK
    runs -- whether a detected drift actually triggers a retrain is a
    separate, runtime-toggleable flag an admin flips from the panel
    (see services/drift_monitor.py's state file), so pausing/resuming
    auto-retraining doesn't need an app restart even though starting
    the check job itself does.
    """
    if not app.config.get('LIVE_RETRAIN_ENABLED', False):
        app.logger.info("LIVE_RETRAIN_ENABLED=false -- drift-check scheduler not started.")
        return

    from .drift_monitor import run_scheduled_drift_check

    def _drift_job():
        with app.app_context():
            try:
                result = run_scheduled_drift_check(app)
                app.logger.info(f"[live-retrain] {result['reason']}")
            except Exception as e:
                app.logger.error(f"[live-retrain] scheduled drift check failed: {e}")

    interval = app.config.get('LIVE_RETRAIN_CHECK_INTERVAL_MINUTES', 360)
    scheduler.add_job(_drift_job, 'interval', minutes=interval, id='live_retrain_drift_check')
    app.logger.info(f"[live-retrain] drift-check scheduler started, checking every {interval} minute(s).")


def _add_scheduled_reports_job(app, scheduler):
    """Scheduled Reports: periodic check for due report schedules,
    gated by SCHEDULED_REPORTS_ENABLED same as the jobs above are
    gated by their own *_ENABLED flags.
    """
    if not app.config.get('SCHEDULED_REPORTS_ENABLED', False):
        app.logger.info("SCHEDULED_REPORTS_ENABLED=false -- scheduled-reports scheduler not started.")
        return

    from .scheduled_reports import run_due_report_schedules

    def _reports_job():
        with app.app_context():
            try:
                results = run_due_report_schedules(app)
                app.logger.info(f"[scheduled-reports] checked={results['checked']} due={results['due']} "
                                 f"sent={results['sent']} errors={results['errors']}")
            except Exception as e:
                app.logger.error(f"[scheduled-reports] scheduled check failed: {e}")

    interval = app.config.get('SCHEDULED_REPORTS_CHECK_INTERVAL_MINUTES', 60)
    scheduler.add_job(_reports_job, 'interval', minutes=interval, id='scheduled_reports_check')
    app.logger.info(f"[scheduled-reports] scheduler started, checking every {interval} minute(s).")


def _add_notification_jobs(app, scheduler):
    """Charging Reminder + Maintenance Reminder: two independent checks
    (see services/notifications.py), gated by their own *_ENABLED flags
    same as every other job here. Low Battery Alerts and Battery Health
    Warning don't need a scheduler job at all -- they're checked
    synchronously right when the triggering data (a trip simulation, a
    SOH reading) is saved, in api/trip.py and api/vehicles.py.
    """
    from .notifications import check_and_send_charging_reminders, check_and_send_maintenance_reminders

    if app.config.get('CHARGING_REMINDERS_ENABLED', True):
        def _charging_job():
            with app.app_context():
                try:
                    results = check_and_send_charging_reminders(app)
                    app.logger.info(f"[charging-reminders] checked={results['checked']} sent={results['sent']}")
                except Exception as e:
                    app.logger.error(f"[charging-reminders] scheduled check failed: {e}")

        interval = app.config.get('CHARGING_REMINDER_CHECK_INTERVAL_MINUTES', 10)
        scheduler.add_job(_charging_job, 'interval', minutes=interval, id='charging_reminders_check')
        app.logger.info(f"[charging-reminders] scheduler started, checking every {interval} minute(s).")
    else:
        app.logger.info("CHARGING_REMINDERS_ENABLED=false -- charging-reminder scheduler not started.")

    if app.config.get('MAINTENANCE_REMINDERS_ENABLED', True):
        def _maintenance_job():
            with app.app_context():
                try:
                    results = check_and_send_maintenance_reminders(app)
                    app.logger.info(f"[maintenance-reminders] checked={results['checked']} sent={results['sent']}")
                except Exception as e:
                    app.logger.error(f"[maintenance-reminders] scheduled check failed: {e}")

        interval = app.config.get('MAINTENANCE_REMINDER_CHECK_INTERVAL_MINUTES', 360)
        scheduler.add_job(_maintenance_job, 'interval', minutes=interval, id='maintenance_reminders_check')
        app.logger.info(f"[maintenance-reminders] scheduler started, checking every {interval} minute(s).")
    else:
        app.logger.info("MAINTENANCE_REMINDERS_ENABLED=false -- maintenance-reminder scheduler not started.")
