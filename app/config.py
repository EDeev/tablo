import os

from dotenv import load_dotenv

load_dotenv()


def _database_url():
    if os.getenv('DATABASE_URL'):
        return os.getenv('DATABASE_URL')
    return (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 1800,
    }
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024
    WTF_CSRF_ENABLED = True
