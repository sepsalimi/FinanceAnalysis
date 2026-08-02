# Backend

FastAPI + SQLAlchemy 2 + Alembic + Dramatiq worker for the household finance platform.

```bash
cd backend
uv pip install -e ".[dev]"
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload --port 8000
# worker
dramatiq app.workers.tasks --processes 1 --threads 2
pytest
```
