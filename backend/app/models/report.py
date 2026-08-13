"""Reports phase: Scheduled Reports (recurring report configs) and
Report History (a log of every report actually generated, whether
downloaded manually or emailed on a schedule).
"""
from datetime import datetime, timedelta
from .. import db

REPORT_TYPES = ('predictions', 'trips', 'summary')
REPORT_FORMATS = ('csv', 'xlsx', 'json', 'pdf')
REPORT_FREQUENCIES = ('daily', 'weekly', 'monthly')

_FREQUENCY_TIMEDELTA = {
    'daily': timedelta(days=1),
    'weekly': timedelta(weeks=1),
    'monthly': timedelta(days=30),  # documented approximation, not calendar-month-aware
}


class ReportSchedule(db.Model):
    """A recurring report a user wants emailed to themselves. Checked
    by the scheduled-reports background job (see services/scheduler.py)
    -- 'due' is computed from last_sent_at + frequency rather than
    storing a separate next_run_at column, so changing the frequency
    takes effect immediately without needing to also recompute a
    stored next-run date.
    """
    __tablename__ = 'report_schedules'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    name = db.Column(db.String(120), nullable=False)
    report_type = db.Column(db.String(20), nullable=False, default='predictions')
    format = db.Column(db.String(10), nullable=False, default='csv')
    frequency = db.Column(db.String(10), nullable=False, default='weekly')
    enabled = db.Column(db.Boolean, default=True)

    last_sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='report_schedules')

    def is_due(self, now=None):
        now = now or datetime.utcnow()
        # self.enabled can be None on a transient (constructed but not
        # yet committed/flushed) object -- the column's default=True
        # only actually applies at flush time, not at __init__. Only
        # an explicit False should count as disabled; None should
        # behave like the eventual default (True).
        if self.enabled is False:
            return False
        if self.last_sent_at is None:
            return True
        return now - self.last_sent_at >= _FREQUENCY_TIMEDELTA[self.frequency]

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'report_type': self.report_type,
            'format': self.format,
            'frequency': self.frequency,
            'enabled': self.enabled,
            'last_sent_at': self.last_sent_at.isoformat() if self.last_sent_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ReportHistory(db.Model):
    """A log entry for every report actually generated -- manual
    downloads (Excel/JSON/CSV/PDF from the reports page) AND scheduled
    email sends both write one of these, so Report History is a
    complete record regardless of how the report was produced.
    """
    __tablename__ = 'report_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('report_schedules.id'), nullable=True)

    report_type = db.Column(db.String(20), nullable=False)
    format = db.Column(db.String(10), nullable=False)
    source = db.Column(db.String(10), nullable=False, default='manual')  # 'manual' or 'scheduled'
    row_count = db.Column(db.Integer, nullable=True)

    delivered_via_email = db.Column(db.Boolean, default=False)
    email_status = db.Column(db.String(200), nullable=True)  # e.g. 'sent', 'mail not configured', an error message

    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='report_history')

    def to_dict(self):
        return {
            'id': self.id,
            'schedule_id': self.schedule_id,
            'report_type': self.report_type,
            'format': self.format,
            'source': self.source,
            'row_count': self.row_count,
            'delivered_via_email': self.delivered_via_email,
            'email_status': self.email_status,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
        }
