from datetime import datetime, timezone
from app.extensions import db
from app.utils.datetime_helpers import iso_utc


class UserRating(db.Model):
    """A rating left by one user about another, e.g. after a successful
    item return/claim transaction. Drives the average shown on User.rating."""
    __tablename__ = 'user_ratings'

    id = db.Column(db.Integer, primary_key=True)
    rater_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rated_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id', ondelete='SET NULL'), nullable=True)
    score = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('rater_id', 'rated_user_id', 'report_id', name='uq_rating_per_report'),
        db.CheckConstraint('score >= 1 AND score <= 5', name='ck_rating_score_range'),
    )

    rater = db.relationship('User', foreign_keys=[rater_id])
    rated_user = db.relationship('User', foreign_keys=[rated_user_id])
    report = db.relationship('Report')

    def to_dict(self):
        return {
            'id': self.id,
            'rater': self.rater.to_dict() if self.rater else None,
            'rated_user_id': self.rated_user_id,
            'report': {'id': self.report.id, 'title': self.report.title} if self.report else None,
            'score': self.score,
            'comment': self.comment,
            'created_at': iso_utc(self.created_at),
        }

    def __repr__(self):
        return f'<UserRating {self.rater_id}->{self.rated_user_id}: {self.score}>'
