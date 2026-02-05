from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func

from app import db
from app.models import Article, Annotation, DifficultPassage

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get user's annotation statistics
    user_annotations = Annotation.query.filter_by(user_id=current_user.id).all()
    total_annotations = len(user_annotations)

    # Calculate average scores given by user
    avg_scores = None
    if total_annotations > 0:
        avg_scores = {
            'mental_effort': sum(a.mental_effort_score for a in user_annotations) / total_annotations,
            'background_knowledge': sum(a.background_knowledge_score for a in user_annotations) / total_annotations,
            'emotional_drain': sum(a.emotional_drain_score for a in user_annotations) / total_annotations,
            'clarity': sum(a.clarity_score for a in user_annotations) / total_annotations,
        }

    # Get total articles and articles needing ratings
    total_articles = Article.query.count()
    articles_rated_by_user = Annotation.query.filter_by(user_id=current_user.id).count()
    articles_remaining = total_articles - articles_rated_by_user

    # Recent annotations
    recent_annotations = Annotation.query.filter_by(user_id=current_user.id)\
        .order_by(Annotation.timestamp_submitted.desc())\
        .limit(5).all()

    return render_template('main/dashboard.html',
                           total_annotations=total_annotations,
                           avg_scores=avg_scores,
                           total_articles=total_articles,
                           articles_remaining=articles_remaining,
                           recent_annotations=recent_annotations)


@main_bp.route('/article/next')
@login_required
def next_article():
    """Get the next article for annotation using priority algorithm."""
    # Find articles user hasn't rated, prioritizing those with fewer ratings
    subquery = db.session.query(
        Article.id,
        func.count(Annotation.id).label('annotation_count')
    ).outerjoin(Annotation).group_by(Article.id).subquery()

    # Get articles user hasn't annotated
    user_annotated = db.session.query(Annotation.article_id)\
        .filter(Annotation.user_id == current_user.id).subquery()

    article = db.session.query(Article)\
        .join(subquery, Article.id == subquery.c.id)\
        .filter(~Article.id.in_(user_annotated))\
        .order_by(subquery.c.annotation_count.asc(), func.random())\
        .first()

    if not article:
        flash('You have rated all available articles!', 'info')
        return redirect(url_for('main.dashboard'))

    return redirect(url_for('main.view_article', article_id=article.id))


@main_bp.route('/article/<int:article_id>')
@login_required
def view_article(article_id):
    article = Article.query.get_or_404(article_id)

    # Check if user already rated this article
    existing_annotation = Annotation.query.filter_by(
        article_id=article_id,
        user_id=current_user.id
    ).first()

    if existing_annotation:
        flash('You have already rated this article.', 'info')
        return redirect(url_for('main.dashboard'))

    return render_template('main/article.html', article=article)


@main_bp.route('/article/<int:article_id>/submit', methods=['POST'])
@login_required
def submit_annotation(article_id):
    article = Article.query.get_or_404(article_id)

    # Check for existing annotation
    existing = Annotation.query.filter_by(
        article_id=article_id,
        user_id=current_user.id
    ).first()

    if existing:
        return jsonify({'error': 'You have already rated this article'}), 400

    try:
        data = request.get_json()

        annotation = Annotation(
            article_id=article_id,
            user_id=current_user.id,
            mental_effort_score=int(data['mental_effort_score']),
            background_knowledge_score=int(data['background_knowledge_score']),
            emotional_drain_score=int(data['emotional_drain_score']),
            clarity_score=int(data['clarity_score']),
            optional_comments=data.get('optional_comments', ''),
            time_spent_seconds=float(data.get('time_spent_seconds', 0)),
            active_time_seconds=float(data.get('active_time_seconds', 0)),
            scroll_depth_percent=float(data.get('scroll_depth_percent', 0)),
            scroll_back_count=int(data.get('scroll_back_count', 0)),
            pause_count=int(data.get('pause_count', 0)),
            mouse_activity_score=float(data.get('mouse_activity_score', 0)),
        )

        db.session.add(annotation)
        db.session.flush()  # Get annotation ID

        # Add difficult passages if any
        difficult_passages = data.get('difficult_passages', [])
        for passage in difficult_passages:
            dp = DifficultPassage(
                annotation_id=annotation.id,
                text_content=passage['text_content'],
                start_offset=int(passage['start_offset']),
                end_offset=int(passage['end_offset'])
            )
            db.session.add(dp)

        db.session.commit()

        return jsonify({'success': True, 'redirect': url_for('main.dashboard')})

    except (KeyError, ValueError) as e:
        db.session.rollback()
        return jsonify({'error': f'Invalid data: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'An error occurred while saving'}), 500
