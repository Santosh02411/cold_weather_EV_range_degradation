"""
FEAT-3: the actual check-and-send logic for cold-snap alerts, called
periodically by the scheduler (services/scheduler.py).

Design choices worth being explicit about:
  - Uses the SAME weather-fetch + cache path as the rest of the app
    (weather.py's fetch_openweathermap/get_demo_weather + the INFRA-3
    TTL cache) rather than a separate weather integration, so alert
    checks don't multiply the app's real API call volume beyond what
    caching already accounts for.
  - If MAIL_USERNAME/MAIL_PASSWORD aren't configured, this does NOT
    silently no-op -- it logs exactly what it would have sent. A
    feature that quietly does nothing when misconfigured is worse than
    one that's loud about not being able to do its job, consistent with
    every other "fail soft but say so" pattern in this project.
  - Cooldown is tracked per-subscription (last_alert_sent_at), not
    globally, so a persistent multi-day cold snap sends one alert every
    ALERT_COOLDOWN_HOURS, not one alert per scheduler tick.
"""
from datetime import datetime, timedelta


def check_and_send_alerts(app):
    """Called by the scheduler on each tick. Must be called with an app
    already available (the scheduler wraps this in `with app.app_context()`)
    since it needs DB and mail access, both Flask-extension-bound.
    """
    from ..models.alert_subscription import AlertSubscription
    from .. import db, mail
    from ..api.weather import fetch_openweathermap, get_demo_weather
    from . import cache
    from flask_mail import Message

    api_key = app.config.get('OPENWEATHERMAP_API_KEY', 'demo')
    cooldown = timedelta(hours=app.config.get('ALERT_COOLDOWN_HOURS', 12))
    mail_configured = bool(app.config.get('MAIL_USERNAME') and app.config.get('MAIL_PASSWORD'))

    subscriptions = AlertSubscription.query.filter_by(enabled=True).all()
    results = {'checked': 0, 'triggered': 0, 'sent': 0, 'skipped_cooldown': 0, 'errors': 0}

    # Group by location so N subscriptions to the same city only cost
    # one weather lookup per tick, not N -- the cache would also
    # collapse this, but grouping avoids even the cache-lookup overhead
    # and keeps the intent explicit in the code.
    by_location = {}
    for sub in subscriptions:
        by_location.setdefault(sub.location, []).append(sub)

    for location, subs in by_location.items():
        results['checked'] += len(subs)
        try:
            def _fetch():
                if api_key and api_key != 'demo':
                    w, err = fetch_openweathermap(location, api_key)
                    return w if not err else get_demo_weather(location)
                return get_demo_weather(location)

            ttl = app.config.get('WEATHER_CACHE_TTL_SECONDS', 600)
            weather, _ = cache.get_or_set(f"alert-weather:{location.lower()}", ttl, _fetch) if ttl > 0 else (_fetch(), False)
            temp = weather['temperature_c']
        except Exception as e:
            print(f"[ERROR] Alert weather check failed for '{location}': {e}")
            results['errors'] += len(subs)
            continue

        for sub in subs:
            sub.last_checked_at = datetime.utcnow()
            sub.last_checked_temperature_c = temp

            if temp > sub.temperature_threshold_c:
                continue  # not a cold snap for this subscription's threshold

            results['triggered'] += 1
            if sub.last_alert_sent_at and (datetime.utcnow() - sub.last_alert_sent_at) < cooldown:
                results['skipped_cooldown'] += 1
                continue

            subject = f"Cold snap alert: {location} is at {temp:.1f}\u00b0C"
            body = (
                f"{location} has dropped to {temp:.1f}\u00b0C, at or below your "
                f"alert threshold of {sub.temperature_threshold_c:.1f}\u00b0C.\n\n"
                f"Cold weather can significantly reduce your EV's range -- check "
                f"a prediction before heading out.\n\n"
                f"(You're receiving this because you subscribed to cold-snap "
                f"alerts for {location}.)"
            )

            if not mail_configured:
                print(f"[ALERT-WOULD-SEND] (MAIL_USERNAME/PASSWORD not configured) "
                      f"To user {sub.user_id}: {subject}")
            else:
                try:
                    msg = Message(subject=subject, recipients=[sub.user.email], body=body)
                    mail.send(msg)
                    results['sent'] += 1
                except Exception as e:
                    print(f"[ERROR] Failed to send alert email to user {sub.user_id}: {e}")
                    results['errors'] += 1
                    continue

            sub.last_alert_sent_at = datetime.utcnow()

    db.session.commit()
    return results
