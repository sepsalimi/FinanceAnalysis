"""FastAPI application entrypoint for the household finance platform."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()
settings = get_settings()

app = FastAPI(
    title="Household Financial Intelligence API",
    version="0.1.0",
    description="Database-driven household finance platform. PostgreSQL is the source of truth.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https://.*\.(onrender\.com|github\.io)"
    if settings.is_production
    else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _mount_static_ui() -> None:
    """Serve the exported Next.js UI from the same origin in cloud deploys."""
    candidates = [
        Path(settings.static_site_dir),
        Path(__file__).resolve().parent.parent / "static_site",
        Path("/app/static_site"),
    ]
    static_dir = next((path for path in candidates if path.is_dir()), None)
    if static_dir is None:
        return

    assets_dir = static_dir / "_next"
    if assets_dir.is_dir():
        app.mount("/_next", StaticFiles(directory=assets_dir), name="next-assets")

    icons_dir = static_dir / "icons"
    if icons_dir.is_dir():
        app.mount("/icons", StaticFiles(directory=icons_dir), name="icons")

    @app.get("/manifest.webmanifest")
    def manifest() -> FileResponse:
        return FileResponse(static_dir / "manifest.webmanifest")

    @app.get("/sw.js")
    def service_worker() -> FileResponse:
        return FileResponse(static_dir / "sw.js", media_type="application/javascript")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    @app.get("/{full_path:path}")
    def spa(full_path: str) -> FileResponse:
        target = static_dir / full_path
        if target.is_file():
            return FileResponse(target)
        index_page = static_dir / full_path / "index.html"
        if index_page.is_file():
            return FileResponse(index_page)
        return FileResponse(static_dir / "index.html")


_mount_static_ui()
