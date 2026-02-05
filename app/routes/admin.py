import csv
import json
from io import StringIO
from datetime import datetime
from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from sqlalchemy import func

from app import db
from app.models import Article, Annotation, User, DifficultPassage

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@admin_required
def dashboard():
    # Get statistics
    total_articles = Article.query.count()
    total_annotations = Annotation.query.count()
    total_users = User.query.filter_by(is_admin=False).count()

    # Articles needing more annotations (< 5 ratings)
    articles_needing_ratings = db.session.query(
        Article.id, Article.title, func.count(Annotation.id).label('count')
    ).outerjoin(Annotation).group_by(Article.id)\
        .having(func.count(Annotation.id) < 5).count()

    # Average scores across all annotations
    avg_scores = None
    if total_annotations > 0:
        avg_scores = db.session.query(
            func.avg(Annotation.mental_effort_score).label('mental_effort'),
            func.avg(Annotation.background_knowledge_score).label('background_knowledge'),
            func.avg(Annotation.emotional_drain_score).label('emotional_drain'),
            func.avg(Annotation.clarity_score).label('clarity'),
        ).first()

    # Annotations per day (last 30 days)
    annotations_by_day = db.session.query(
        func.date(Annotation.timestamp_submitted).label('date'),
        func.count(Annotation.id).label('count')
    ).group_by(func.date(Annotation.timestamp_submitted))\
        .order_by(func.date(Annotation.timestamp_submitted).desc())\
        .limit(30).all()

    return render_template('admin/dashboard.html',
                           total_articles=total_articles,
                           total_annotations=total_annotations,
                           total_users=total_users,
                           articles_needing_ratings=articles_needing_ratings,
                           avg_scores=avg_scores,
                           annotations_by_day=annotations_by_day)


@admin_bp.route('/upload', methods=['GET', 'POST'])
@admin_required
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash('No file uploaded.', 'error')
            return redirect(url_for('admin.upload'))

        filename = file.filename.lower()
        content = file.read().decode('utf-8')

        try:
            if filename.endswith('.json'):
                articles = parse_json_articles(content)
            elif filename.endswith('.csv'):
                articles = parse_csv_articles(content)
            else:
                flash('Unsupported file format. Please upload JSON or CSV.', 'error')
                return redirect(url_for('admin.upload'))

            added_count = 0
            for article_data in articles:
                article = Article(
                    title=article_data['title'],
                    source=article_data.get('source', ''),
                    url=article_data.get('url', ''),
                    publish_date=parse_date(article_data.get('publish_date')),
                    full_text=article_data['full_text']
                )
                db.session.add(article)
                added_count += 1

            db.session.commit()
            flash(f'Successfully added {added_count} articles.', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Error parsing file: {str(e)}', 'error')

        return redirect(url_for('admin.upload'))

    return render_template('admin/upload.html')


def parse_json_articles(content):
    data = json.loads(content)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'articles' in data:
        return data['articles']
    else:
        raise ValueError('JSON must be an array or object with "articles" key')


def parse_csv_articles(content):
    articles = []
    reader = csv.DictReader(StringIO(content))
    for row in reader:
        articles.append({
            'title': row.get('title', ''),
            'source': row.get('source', ''),
            'url': row.get('url', ''),
            'publish_date': row.get('publish_date', ''),
            'full_text': row.get('full_text', '')
        })
    return articles


def parse_date(date_str):
    if not date_str:
        return None
    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%B %d, %Y']:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


@admin_bp.route('/articles')
@admin_required
def articles_list():
    articles = db.session.query(
        Article,
        func.count(Annotation.id).label('annotation_count')
    ).outerjoin(Annotation).group_by(Article.id)\
        .order_by(func.count(Annotation.id).asc()).all()

    return render_template('admin/articles.html', articles=articles)


@admin_bp.route('/article/<int:article_id>/annotations')
@admin_required
def article_annotations(article_id):
    article = Article.query.get_or_404(article_id)
    annotations = Annotation.query.filter_by(article_id=article_id)\
        .order_by(Annotation.timestamp_submitted.desc()).all()

    return render_template('admin/annotations.html',
                           article=article,
                           annotations=annotations)


@admin_bp.route('/export')
@admin_required
def export_csv():
    output = StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        'annotation_id', 'article_id', 'article_title', 'user_id', 'username',
        'mental_effort_score', 'background_knowledge_score', 'emotional_drain_score',
        'clarity_score', 'optional_comments', 'time_spent_seconds', 'active_time_seconds',
        'scroll_depth_percent', 'scroll_back_count', 'pause_count', 'mouse_activity_score',
        'timestamp_submitted', 'difficult_passages'
    ])

    # Data rows
    annotations = Annotation.query.all()
    for a in annotations:
        # Get difficult passages as JSON string
        passages = [{'text': p.text_content, 'start': p.start_offset, 'end': p.end_offset}
                    for p in a.difficult_passages]
        passages_json = json.dumps(passages) if passages else ''

        writer.writerow([
            a.id, a.article_id, a.article.title, a.user_id, a.user.username,
            a.mental_effort_score, a.background_knowledge_score, a.emotional_drain_score,
            a.clarity_score, a.optional_comments or '', a.time_spent_seconds,
            a.active_time_seconds, a.scroll_depth_percent, a.scroll_back_count,
            a.pause_count, a.mouse_activity_score,
            a.timestamp_submitted.isoformat() if a.timestamp_submitted else '',
            passages_json
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=annotations_export.csv'}
    )
