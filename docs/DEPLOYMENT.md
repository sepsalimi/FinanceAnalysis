# Deployment Guidance

1. Set strong secrets in environment (never commit).
2. Use managed PostgreSQL and Redis.
3. Point `S3_*` at AWS S3 or compatible storage with encryption.
4. Run API and worker as separate processes/containers.
5. Terminate TLS at the reverse proxy; enable secure cookies.
6. Run `alembic upgrade head` and `python -m app.db.seed` on deploy.
7. Configure real `LLM_PROVIDER` credentials server-side only.
8. Do not claim regulatory compliance without a formal review.
