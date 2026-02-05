import os
from dotenv import load_dotenv

load_dotenv()

def get_database_url():
    """Get database URL, fixing postgres:// to postgresql:// for SQLAlchemy."""
    url = os.environ.get('DATABASE_URL')
    if url:
        # Railway/Render use postgres:// but SQLAlchemy needs postgresql://
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql://', 1)
        return url
    return 'sqlite:///cognitive_load.db'

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
