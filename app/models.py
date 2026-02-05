from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from app import db, login_manager


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)

    annotations = db.relationship('Annotation', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Article(db.Model):
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    source = db.Column(db.String(200))
    url = db.Column(db.String(1000))
    publish_date = db.Column(db.Date)
    full_text = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    annotations = db.relationship('Annotation', backref='article', lazy='dynamic')

    def annotation_count(self):
        return self.annotations.count()

    def average_scores(self):
        annotations = self.annotations.all()
        if not annotations:
            return None

        return {
            'mental_effort': sum(a.mental_effort_score for a in annotations) / len(annotations),
            'background_knowledge': sum(a.background_knowledge_score for a in annotations) / len(annotations),
            'emotional_drain': sum(a.emotional_drain_score for a in annotations) / len(annotations),
            'clarity': sum(a.clarity_score for a in annotations) / len(annotations),
        }

    def __repr__(self):
        return f'<Article {self.title[:50]}>'


class Annotation(db.Model):
    __tablename__ = 'annotations'

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Rating scores (1-10 scale)
    mental_effort_score = db.Column(db.Integer, nullable=False)
    background_knowledge_score = db.Column(db.Integer, nullable=False)
    emotional_drain_score = db.Column(db.Integer, nullable=False)
    clarity_score = db.Column(db.Integer, nullable=False)

    optional_comments = db.Column(db.Text)

    # Tracking metrics
    time_spent_seconds = db.Column(db.Float)
    active_time_seconds = db.Column(db.Float)
    scroll_depth_percent = db.Column(db.Float)
    scroll_back_count = db.Column(db.Integer)
    pause_count = db.Column(db.Integer)
    mouse_activity_score = db.Column(db.Float)

    timestamp_submitted = db.Column(db.DateTime, default=datetime.utcnow)

    difficult_passages = db.relationship('DifficultPassage', backref='annotation',
                                         lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('article_id', 'user_id', name='unique_user_article_annotation'),
    )

    def __repr__(self):
        return f'<Annotation user={self.user_id} article={self.article_id}>'


class DifficultPassage(db.Model):
    __tablename__ = 'difficult_passages'

    id = db.Column(db.Integer, primary_key=True)
    annotation_id = db.Column(db.Integer, db.ForeignKey('annotations.id'), nullable=False)
    text_content = db.Column(db.Text, nullable=False)
    start_offset = db.Column(db.Integer, nullable=False)
    end_offset = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<DifficultPassage {self.text_content[:30]}>'
