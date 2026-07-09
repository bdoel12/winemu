from datetime import datetime, timezone
from app.extensions import db
from app.utils.datetime_helpers import iso_utc


class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    type = db.Column(db.Enum('hilang', 'ditemukan'), nullable=False)  # hilang | ditemukan
    status = db.Column(db.Enum('aktif', 'proses', 'selesai', 'ditutup'), default='aktif')
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    verification_question = db.Column(db.String(300))  # Pertanyaan publik, ditampilkan ke calon pengklaim
    verification_answer = db.Column(db.String(500))    # Jawaban benar, hanya pemilik & admin yang tahu
    location_name = db.Column(db.String(200))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    date_occurred = db.Column(db.DateTime)
    reward = db.Column(db.String(200))
    contact_info = db.Column(db.String(200))
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    share_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    media = db.relationship('ReportMedia', backref='report', lazy='dynamic',
                            cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='report', lazy='dynamic',
                               cascade='all, delete-orphan')
    likes = db.relationship('ReportLike', backref='report', lazy='dynamic',
                            cascade='all, delete-orphan')
    bookmarks = db.relationship('Bookmark', backref='report', lazy='dynamic',
                                cascade='all, delete-orphan')
    category = db.relationship('Category', backref='reports')

    def to_dict(self, current_user_id=None):
        media_list = [m.to_dict() for m in self.media.order_by(ReportMedia.order).all()]
        primary_image = next((m['url'] for m in media_list if m['type'] == 'image'), None)
        primary_video = next((m['url'] for m in media_list if m['type'] == 'video'), None)

        is_liked = False
        if current_user_id:
            is_liked = ReportLike.query.filter_by(
                report_id=self.id, user_id=current_user_id
            ).first() is not None

        # Jawaban verifikasi hanya boleh dilihat oleh pemilik laporan (atau admin,
        # yang dicek terpisah di layer endpoint). Pengklaim hanya boleh melihat
        # pertanyaannya, tidak pernah jawabannya, agar sistem verifikasi tetap berguna.
        is_owner = current_user_id is not None and current_user_id == self.user_id

        data = {
            'id': self.id,
            'user_id': self.user_id,
            'author': self.author.to_dict() if self.author else None,
            'type': self.type,
            'status': self.status,
            'title': self.title,
            'description': self.description,
            'category': self.category.to_dict() if self.category else None,
            'location_name': self.location_name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'date_occurred': iso_utc(self.date_occurred),
            'reward': self.reward,
            'verification_question': self.verification_question,
            'primary_image': primary_image,
            'primary_video': primary_video,
            'media': media_list,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'share_count': self.share_count,
            'view_count': self.view_count,
            'is_verified': self.is_verified,
            'is_liked': is_liked,
            'created_at': iso_utc(self.created_at),
            'updated_at': iso_utc(self.updated_at),
        }
        if is_owner:
            data['verification_answer'] = self.verification_answer
        return data

    def __repr__(self):
        return f'<Report {self.id} {self.type}: {self.title}>'


class ReportMedia(db.Model):
    __tablename__ = 'report_media'

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id', ondelete='CASCADE'), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    type = db.Column(db.Enum('image', 'video'), default='image')
    filename = db.Column(db.String(255))
    size = db.Column(db.Integer)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'type': self.type,
            'filename': self.filename,
            'order': self.order,
        }


class ReportLike(db.Model):
    __tablename__ = 'report_likes'

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint('report_id', 'user_id'),)
