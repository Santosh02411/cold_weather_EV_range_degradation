"""Favorite Vehicles and Recently Viewed Vehicles."""
from datetime import datetime
from .. import db


class FavoriteVehicle(db.Model):
    __tablename__ = 'favorite_vehicles'
    __table_args__ = (db.UniqueConstraint('user_id', 'vehicle_id', name='uq_favorite_user_vehicle'),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('ev_vehicles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='favorite_vehicles')
    vehicle = db.relationship('EVVehicle')


class RecentlyViewedVehicle(db.Model):
    __tablename__ = 'recently_viewed_vehicles'
    __table_args__ = (db.UniqueConstraint('user_id', 'vehicle_id', name='uq_recent_user_vehicle'),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('ev_vehicles.id'), nullable=False)
    # One row per (user, vehicle) -- re-viewing just bumps viewed_at
    # rather than creating a new row every time, so "recently viewed"
    # shows each vehicle once, most-recent-view-first, not a raw view log.
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='recently_viewed_vehicles')
    vehicle = db.relationship('EVVehicle')


def record_view(user_id, vehicle_id, max_kept=20):
    """Upsert a recently-viewed row and prune old entries beyond
    max_kept, so this table doesn't grow unbounded for an active user.
    """
    existing = RecentlyViewedVehicle.query.filter_by(user_id=user_id, vehicle_id=vehicle_id).first()
    if existing:
        existing.viewed_at = datetime.utcnow()
    else:
        db.session.add(RecentlyViewedVehicle(user_id=user_id, vehicle_id=vehicle_id))
    db.session.commit()

    all_views = RecentlyViewedVehicle.query.filter_by(user_id=user_id) \
        .order_by(RecentlyViewedVehicle.viewed_at.desc()).all()
    for stale in all_views[max_kept:]:
        db.session.delete(stale)
    if len(all_views) > max_kept:
        db.session.commit()
