from datetime import datetime, timezone
from app.extensions import db
from app.utils.datetime_helpers import iso_utc


class Claim(db.Model):
    """
    Represents a claim of ownership made by a user on a 'ditemukan' (found) report,
    or a claim that the user found the lost item on a 'hilang' (lost) report.
    Used to drive the conflict resolution / dispute workflow in the admin panel.
    """
    __tablename__ = 'claims'

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id', ondelete='CASCADE'), nullable=False, index=True)
    claimant_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    answer = db.Column(db.Text)  # Jawaban dari pengklaim terhadap verification_question
    status = db.Column(db.Enum('pending', 'approved', 'rejected', 'disputed'), default='pending')
    priority = db.Column(db.Enum('rendah', 'sedang', 'tinggi'), default='sedang')
    admin_notes = db.Column(db.Text)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    resolved_at = db.Column(db.DateTime)
    deadline = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Serah terima barang - diisi setelah klaim disetujui (status='approved')
    handover_method = db.Column(db.Enum('cod', 'titik_aman', 'kurir'), nullable=True)
    handover_location = db.Column(db.String(300))   # Nama lokasi titik aman
    handover_tracking = db.Column(db.String(200))   # Nomor resi / link tracking kurir
    handover_status = db.Column(db.Enum('menunggu_metode', 'dalam_proses', 'selesai'), default='menunggu_metode')
    handover_completed_at = db.Column(db.DateTime)

    report = db.relationship('Report', backref=db.backref('claims', lazy='dynamic', cascade='all, delete-orphan'))
    claimant = db.relationship('User', foreign_keys=[claimant_id])
    resolver = db.relationship('User', foreign_keys=[resolved_by])

    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'report': {
                'id': self.report.id,
                'title': self.report.title,
                'type': self.report.type,
                'primary_image': next((m.url for m in self.report.media.all() if m.type == 'image'), None),
                'verification_question': self.report.verification_question,
                'verification_answer': self.report.verification_answer,
                'latitude': self.report.latitude,
                'longitude': self.report.longitude,
                'location_name': self.report.location_name,
            } if self.report else None,
            'claimant': self.claimant.to_dict() if self.claimant else None,
            'reporter': self.report.author.to_dict() if self.report and self.report.author else None,
            'answer': self.answer,
            'status': self.status,
            'priority': self.priority,
            'admin_notes': self.admin_notes,
            'resolved_by': self.resolver.to_dict() if self.resolver else None,
            'resolved_at': iso_utc(self.resolved_at),
            'deadline': iso_utc(self.deadline),
            'created_at': iso_utc(self.created_at),
            'handover_method': self.handover_method,
            'handover_location': self.handover_location,
            'handover_tracking': self.handover_tracking,
            'handover_status': self.handover_status,
            'handover_completed_at': iso_utc(self.handover_completed_at),
        }

    def __repr__(self):
        return f'<Claim {self.id} report={self.report_id} status={self.status}>'
