from datetime import datetime, timezone
from app.extensions import db
from app.utils.datetime_helpers import iso_utc


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    icon = db.Column(db.String(100))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'icon': self.icon,
            'description': self.description,
        }


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]),
                              lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'user_id': self.user_id,
            'author': self.author.to_dict() if self.author else None,
            'parent_id': self.parent_id,
            'content': self.content,
            'created_at': iso_utc(self.created_at),
        }


class Bookmark(db.Model):
    __tablename__ = 'bookmarks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint('user_id', 'report_id'),)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'report_id': self.report_id,
            'report': self.report.to_dict() if self.report else None,
            'created_at': iso_utc(self.created_at),
        }


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    type = db.Column(db.String(50), nullable=False)  # like, comment, mention, found, system
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    data = db.Column(db.JSON)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    actor = db.relationship('User', foreign_keys=[actor_id])

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'is_read': self.is_read,
            'actor': self.actor.to_dict() if self.actor else None,
            'created_at': iso_utc(self.created_at),
        }


class Conversation(db.Model):
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id', ondelete='CASCADE'), nullable=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.Enum('pending', 'active', 'closed'), default='active')
    last_message_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user1 = db.relationship('User', foreign_keys=[user1_id])
    user2 = db.relationship('User', foreign_keys=[user2_id])
    report = db.relationship('Report')
    messages = db.relationship('Message', backref='conversation', lazy='dynamic',
                               cascade='all, delete-orphan')

    def to_dict(self, current_user_id=None):
        other_user = self.user2 if current_user_id == self.user1_id else self.user1
        last_msg = self.messages.order_by(Message.created_at.desc()).first()
        unread = self.messages.filter_by(is_read=False).filter(
            Message.sender_id != current_user_id
        ).count() if current_user_id else 0
        report_data = None
        if self.report:
            media_list = [m.to_dict() for m in self.report.media.all()]
            primary_image = next((m['url'] for m in media_list if m['type'] == 'image'), None)
            report_data = {
                'id': self.report.id,
                'title': self.report.title,
                'type': self.report.type,
                'status': self.report.status,
                'primary_image': primary_image,
                'verification_question': self.report.verification_question,
                'owner_id': self.report.user_id,
            }

        return {
            'id': self.id,
            'report': report_data,
            'other_user': other_user.to_dict() if other_user else None,
            'status': self.status,
            'last_message': last_msg.to_dict() if last_msg else None,
            'unread_count': unread,
            'last_message_at': iso_utc(self.last_message_at),
            'created_at': iso_utc(self.created_at),
        }


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='text')  # text, image, system
    is_read = db.Column(db.Boolean, default=False)
    is_pinned = db.Column(db.Boolean, default=False)
    reply_to_id = db.Column(db.Integer, db.ForeignKey('messages.id', ondelete='SET NULL'), nullable=True)
    reply_to_content = db.Column(db.Text, nullable=True)
    reply_to_sender = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender_id': self.sender_id,
            'sender': self.sender.to_dict() if self.sender else None,
            'content': self.content,
            'type': self.type,
            'is_read': self.is_read,
            'is_pinned': getattr(self, 'is_pinned', False) or False,
            'reply_to_id': getattr(self, 'reply_to_id', None),
            'reply_to_content': getattr(self, 'reply_to_content', None),
            'reply_to_sender': getattr(self, 'reply_to_sender', None),
            'created_at': iso_utc(self.created_at),
        }


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.Integer)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
