# CV Matcher – Job Recommendation System

End-to-end job recommendation platform with a FastAPI backend, PostgreSQL, FAISS embeddings, and a modern React frontend.

## Features
- Hybrid recommendation (FAISS + filtering + ML re‑ranking)
- FastAPI backend with JWT auth, rate limiting, and analytics
- React frontend with candidate and recruiter dashboards
- Embeddings via `sentence-transformers`

## Backend: Quick Start

Prerequisites: Python 3.10+, PostgreSQL (or change DB URL to SQLite for local testing).

```bash
# Create and activate a virtual environment
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# (Optional) set env vars
# cp .env.example .env  # if available
# export DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/cvmatcher

# Run API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000` and API docs `http://localhost:8000/docs`.

### Database & Migrations

```bash
alembic upgrade head
```

### Build/Refresh Embeddings

```bash
python -m embeddings.build_index
```

### Seeding (optional)

```bash
python scripts/init_db.py
python scripts/seed_matching_demo.py
```

## Frontend: Run locally

The React app lives in `frontend/`.

```bash
cd frontend
# Use Node 18+ and npm 9+
npm install
npm start
# App runs on http://localhost:3000
```

If your backend runs on a different host/port, update `frontend/src/api.js` (`API_BASE_URL`).

## Testing

```bash
pytest -q
```

## Production Notes
- Run behind a process manager (e.g., `gunicorn -k uvicorn.workers.UvicornWorker`)
- Build and serve the frontend (`npm run build`) via a reverse proxy or static host
- Configure secrets, CORS, and DB connection using environment variables



