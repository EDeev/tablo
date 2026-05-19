from app import db
from datetime import datetime

class Schedule(db.Model):
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    data = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subject_configs = db.relationship('SubjectConfig', backref='schedule',
                                      lazy='dynamic', cascade='all, delete-orphan')
    shares = db.relationship('Share', backref='schedule', lazy='dynamic',
                             cascade='all, delete-orphan')


COMPLETION_TYPES = ['Зачёт', 'Диф. зачёт', 'Экзамен']


class SubjectConfig(db.Model):
    __tablename__ = 'subject_configs'

    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False)
    subject_name = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text, nullable=True)
    hidden = db.Column(db.Boolean, nullable=False, default=False)
    completion_type = db.Column(db.String(32), nullable=True)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    sdo_url = db.Column(db.Text, nullable=True)

    metrics = db.relationship('Metric', backref='subject_config',
                              order_by='Metric.grid_row, Metric.grid_col, Metric.id',
                              cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('schedule_id', 'subject_name', name='uq_schedule_subject'),
    )
