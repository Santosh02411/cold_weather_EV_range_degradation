from datetime import datetime
from .. import db

class Dataset(db.Model):
    __tablename__ = 'datasets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    num_rows = db.Column(db.Integer, nullable=True)
    num_columns = db.Column(db.Integer, nullable=True)
    columns = db.Column(db.Text, nullable=True)  # JSON list of column names
    description = db.Column(db.Text, nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    uploader = db.relationship('User', backref='datasets')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'filename': self.filename,
            'file_size': self.file_size,
            'num_rows': self.num_rows,
            'num_columns': self.num_columns,
            'description': self.description,
            'is_processed': self.is_processed,
            'uploaded_by': self.uploaded_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class WeatherLog(db.Model):
    __tablename__ = 'weather_logs'

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False, index=True)
    country = db.Column(db.String(10), nullable=True)
    temperature_c = db.Column(db.Float, nullable=False)
    feels_like_c = db.Column(db.Float, nullable=True)
    humidity = db.Column(db.Float, nullable=True)
    wind_speed_kmh = db.Column(db.Float, nullable=True)
    pressure_hpa = db.Column(db.Float, nullable=True)
    weather_condition = db.Column(db.String(50), nullable=True)
    precipitation = db.Column(db.String(20), nullable=True)
    severity = db.Column(db.String(20), nullable=True)  # mild, moderate, severe, extreme
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'city': self.city,
            'country': self.country,
            'temperature_c': self.temperature_c,
            'feels_like_c': self.feels_like_c,
            'humidity': self.humidity,
            'wind_speed_kmh': self.wind_speed_kmh,
            'pressure_hpa': self.pressure_hpa,
            'weather_condition': self.weather_condition,
            'precipitation': self.precipitation,
            'severity': self.severity,
            'fetched_at': self.fetched_at.isoformat() if self.fetched_at else None,
        }
