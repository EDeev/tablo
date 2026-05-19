from app import db
from datetime import datetime
import uuid

class Share(db.Model):
    __tablename__ = 'shares'

    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # view = только просмотр, edit = совместное редактирование, template = клонирование
    share_type = db.Column(db.String(16), nullable=False, default='view')
    token = db.Column(db.String(36), unique=True, nullable=False,
                      default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    editors = db.relationship('ShareEditor', backref='share', lazy='dynamic',
                              cascade='all, delete-orphan')


class ShareEditor(db.Model):
    __tablename__ = 'share_editors'

    id = db.Column(db.Integer, primary_key=True)
    share_id = db.Column(db.Integer, db.ForeignKey('shares.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('share_id', 'user_id', name='uq_share_editor'),
    )
