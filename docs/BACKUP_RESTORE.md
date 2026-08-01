# Backup and Restore

## PostgreSQL

```bash
# Backup
docker compose exec db pg_dump -U finance finance_dev > backup.sql

# Restore
docker compose exec -T db psql -U finance finance_dev < backup.sql
```

## Object storage

Mirror the MinIO/S3 bucket (`finance-uploads`) with your preferred tool (`mc mirror`, `aws s3 sync`).

## Redis

Redis holds queue state only. Losing Redis may require re-enqueueing failed jobs; financial truth remains in PostgreSQL.
