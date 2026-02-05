# Cognitive Load Article Annotation Application

A Flask-based web application for collecting cognitive load ratings on news articles, with automatic tracking of reading behavior metrics for ML training data collection.

## Features

- **User Authentication**: Register, login, and manage user sessions
- **Article Rating System**: Rate articles on 4 dimensions:
  - Mental Effort (1-10)
  - Background Knowledge Required (1-10)
  - Emotional Drain (1-10)
  - Clarity (1-10)
- **Automatic Reading Metrics Tracking**:
  - Time spent on page (total and active)
  - Scroll depth and scroll-back events
  - Pause detection (> 5 seconds)
  - Mouse activity scoring
- **Text Highlighting**: Mark specific passages as difficult
- **Admin Dashboard**: Upload articles, view statistics, export data
- **Smart Article Selection**: Prioritizes under-rated articles

## Setup Instructions

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize Database

The database is automatically created when you first run the application.

### 4. Create Admin User

```bash
flask create-admin
```

Follow the prompts to enter username, email, and password.

### 5. Run the Application

```bash
python run.py
```

The application will be available at `http://localhost:5000`

## Loading Sample Articles

1. Log in as admin
2. Navigate to Admin Dashboard
3. Click "Upload Articles"
4. Upload `sample_data/sample_articles.json`

## Project Structure

```
articles/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # SQLAlchemy models
│   ├── routes/
│   │   ├── auth.py          # Authentication routes
│   │   ├── main.py          # Article reading & rating
│   │   └── admin.py         # Admin dashboard
│   ├── static/
│   │   ├── css/style.css    # Styling
│   │   └── js/tracker.js    # Reading metrics tracking
│   └── templates/           # Jinja2 templates
├── config.py                # Configuration
├── run.py                   # Entry point
├── requirements.txt         # Dependencies
└── sample_data/             # Test data
```

## Database Models

### Users
- id, username, email, password_hash, is_admin, date_joined

### Articles
- id, title, source, url, publish_date, full_text, date_added

### Annotations
- id, article_id, user_id
- Rating scores (mental_effort, background_knowledge, emotional_drain, clarity)
- Tracking metrics (time_spent, active_time, scroll_depth, scroll_back_count, pause_count, mouse_activity)
- optional_comments, timestamp_submitted

### DifficultPassages
- id, annotation_id, text_content, start_offset, end_offset

## API Endpoints

### Authentication
- `GET/POST /login` - User login
- `GET/POST /register` - User registration
- `GET /logout` - User logout

### Main
- `GET /` - Redirect to dashboard
- `GET /dashboard` - User dashboard with stats
- `GET /article/next` - Get next article to rate
- `GET /article/<id>` - View article for rating
- `POST /article/<id>/submit` - Submit annotation

### Admin (requires admin role)
- `GET /admin/` - Admin dashboard
- `GET/POST /admin/upload` - Bulk article upload
- `GET /admin/articles` - List all articles
- `GET /admin/article/<id>/annotations` - View article annotations
- `GET /admin/export` - Export all data as CSV

## Configuration

Environment variables (or set in `.env` file):

- `SECRET_KEY` - Flask secret key (defaults to dev key)
- `DATABASE_URL` - Database connection string (defaults to SQLite)

## Export Format

CSV export includes:
```
annotation_id, article_id, article_title, user_id, username,
mental_effort_score, background_knowledge_score, emotional_drain_score,
clarity_score, optional_comments, time_spent_seconds, active_time_seconds,
scroll_depth_percent, scroll_back_count, pause_count, mouse_activity_score,
timestamp_submitted, difficult_passages
```

## Deployment (Railway/Render)

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. Deploy to Railway

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Add a PostgreSQL database: "New" → "Database" → "PostgreSQL"
5. Railway auto-detects the `Procfile` and sets up the app
6. Environment variables are auto-configured for the database

### 3. Deploy to Render

1. Go to [render.com](https://render.com) and sign in with GitHub
2. Click "New" → "Web Service"
3. Connect your repository
4. Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app`
5. Add a PostgreSQL database from the dashboard
6. Add environment variable: `DATABASE_URL` (copy from Postgres dashboard)

### 4. Create Admin User (after deploy)

In Railway/Render console or shell:
```bash
flask create-admin
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (auto-set by Railway) |
| `SECRET_KEY` | Random string for session security |

Generate a secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## License

MIT License
