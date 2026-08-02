# Cloud deploy (no local runtime)

GitHub Pages can only host the static UI. The full app (PostgreSQL + API + uploads + LLM settings) needs a cloud host.

## Recommended: Render Blueprint

1. Create a free account at [render.com](https://render.com).
2. Open: [Deploy Blueprint](https://dashboard.render.com/select-repo?type=blueprint) and connect `sepsalimi/FinanceAnalysis`, **or** click the Deploy to Render button in the README.
3. Render reads `render.yaml` and creates:
   - Free Postgres
   - Free Redis-compatible Key Value
   - Free web service building `Dockerfile.cloud` (UI + API on one URL)
4. Wait for the first deploy (several minutes).
5. Open the service URL, e.g. `https://finance-app.onrender.com`.

Then:

1. Register / sign in
2. Complete household onboarding
3. Optional: Household Settings → paste your LLM API key
4. Create accounts and upload CSVs / Splitwise exports
5. On your phone: open the Render URL → Add to Home Screen / Install app

### Free-tier notes

- Free web services sleep after idle; first request can be slow.
- Free Postgres expires after ~30 days unless upgraded.
- Upload files on the free web disk are ephemeral across redeploys. For durable files later, add S3/R2 credentials.
- Background worker is optional; import confirmation already normalizes synchronously.

### LLM keys

Set them in the app under **Household Settings**. They are encrypted in Postgres and never stored in git.

## Alternative hosts

The same `Dockerfile.cloud` works on Fly.io, Railway, or any Docker host with managed Postgres + Redis. Set:

- `DATABASE_URL`
- `REDIS_URL`
- `APP_SECRET_KEY`
- `APP_ENV=production`
