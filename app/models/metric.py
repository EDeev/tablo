from app import db

METRIC_TYPES = [
    'checkpoints', 'progress_bar', 'counter', 'stages',
    'checklist', 'attendance', 'grades', 'deadlines',
    'streak', 'effort_hours', 'rating_history',
]

METRIC_LABELS = {
    'checkpoints':    'Контрольные точки',
    'progress_bar':   'Накопление баллов',
    'counter':        'Счётчик',
    'stages':         'Этапы',
    'checklist':      'Чеклист',
    'attendance':     'Посещаемость',
    'grades':         'Оценки',
    'deadlines':      'Дедлайны',
    'streak':         'Серия',
    'effort_hours':   'Трудозатраты',
    'rating_history': 'История оценок',
}


class Metric(db.Model):
    __tablename__ = 'metrics'

    id                = db.Column(db.Integer, primary_key=True)
    subject_config_id = db.Column(db.Integer, db.ForeignKey('subject_configs.id'), nullable=False)
    type              = db.Column(db.String(32), nullable=False)
    label             = db.Column(db.String(256), nullable=False)
    config            = db.Column(db.JSON, nullable=False, default=dict)
    progress          = db.Column(db.JSON, nullable=False, default=dict)
    grid_col          = db.Column(db.Integer, nullable=False, default=0)
    grid_row          = db.Column(db.Integer, nullable=False, default=0)
    grid_w            = db.Column(db.Integer, nullable=False, default=1)
    grid_h            = db.Column(db.Integer, nullable=False, default=1)
    ai_prompt         = db.Column(db.Text, nullable=True)
