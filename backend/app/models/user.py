from datetime import datetime, timezone
import bcrypt
from app.extensions import db
from app.utils.datetime_helpers import iso_utc


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(500))
    phone = db.Column(db.String(20))
    location = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    role = db.Column(db.String(20), default='user')  # user, admin, moderator
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    response_rate = db.Column(db.Float, default=0.0)
    rating = db.Column(db.Float, default=0.0)
    total_reports = db.Column(db.Integer, default=0)
    total_found = db.Column(db.Integer, default=0)
    reset_token = db.Column(db.String(255))
    reset_token_expires = db.Column(db.DateTime)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    reports = db.relationship('Report', backref='author', lazy='dynamic', foreign_keys='Report.user_id')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic',
                                    foreign_keys='Notification.user_id')
    bookmarks = db.relationship('Bookmark', backref='user', lazy='dynamic')
    messages_sent = db.relationship('Message', backref='sender', lazy='dynamic', foreign_keys='Message.sender_id')

    def set_password(self, password: str):
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    def to_dict(self, include_private=False):
        data = {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'location': self.location,
            'role': self.role,
            'is_verified': self.is_verified,
            'response_rate': self.response_rate,
            'rating': self.rating,
            'total_reports': self.total_reports,
            'total_found': self.total_found,
            'created_at': iso_utc(self.created_at),
        }
        if include_private:
            data['email'] = self.email
            data['phone'] = self.phone
            data['latitude'] = self.latitude
            data['longitude'] = self.longitude
            data['last_login'] = iso_utc(self.last_login)
        return data

    def __repr__(self):
        return f'<User {self.username}>'
