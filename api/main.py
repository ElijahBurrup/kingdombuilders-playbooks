"""
FastAPI application factory for the Playbooks platform.

Mounts all API routers under /api/v1, the legacy backward-compatible
router at /, static files, CORS middleware, and the APScheduler lifespan.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.config import settings

# ---------------------------------------------------------------------------
# Sentry error tracking (no-op if DSN not configured)
# ---------------------------------------------------------------------------
if settings.SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        environment="production",
    )

# ---------------------------------------------------------------------------
# Directory paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent  # Playbooks/
STATIC_DIR = BASE_DIR / "static"
ASSETS_DIR = BASE_DIR / "assets"


# ---------------------------------------------------------------------------
# Lifespan — start/stop APScheduler
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    from api.services.scheduler_service import init_scheduler
    init_scheduler()
    yield
    from api.services.scheduler_service import get_scheduler
    scheduler = get_scheduler()
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    app = FastAPI(
        title="KingdomBuilders Playbooks API",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- API routers (v1) ---
    from api.routers.auth import router as auth_router
    from api.routers.catalog import router as catalog_router
    from api.routers.payments import router as payments_router
    from api.routers.subscribe import router as subscribe_router
    from api.routers.admin import router as admin_router
    from api.routers.discovery import router as discovery_router

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(catalog_router, prefix="/api/v1")
    app.include_router(payments_router, prefix="/api/v1")
    app.include_router(subscribe_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(discovery_router, prefix="/api/v1")

    # --- Legacy backward-compatible router (serves existing HTML pages) ---
    from api.routers.legacy import router as legacy_router
    app.include_router(legacy_router)

    # --- Static files ---
    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    if ASSETS_DIR.is_dir():
        app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

    # --- URL_PREFIX: mount all routes under prefix for subpath deployment ---
    # Cloudflare Worker sends /playbooks/* so we mount everything again
    # under the prefix so routes match both with and without it.
    if settings.URL_PREFIX:
        app.include_router(legacy_router, prefix=settings.URL_PREFIX)

        # API routers under prefix too (e.g. /playbooks/api/v1/...)
        app.include_router(auth_router, prefix=f"{settings.URL_PREFIX}/api/v1")
        app.include_router(catalog_router, prefix=f"{settings.URL_PREFIX}/api/v1")
        app.include_router(payments_router, prefix=f"{settings.URL_PREFIX}/api/v1")
        app.include_router(subscribe_router, prefix=f"{settings.URL_PREFIX}/api/v1")
        app.include_router(admin_router, prefix=f"{settings.URL_PREFIX}/api/v1")
        app.include_router(discovery_router, prefix=f"{settings.URL_PREFIX}/api/v1")

        # Also mount static/assets under the prefix
        if STATIC_DIR.is_dir():
            app.mount(f"{settings.URL_PREFIX}/static", StaticFiles(directory=str(STATIC_DIR)), name="prefixed_static")
        if ASSETS_DIR.is_dir():
            app.mount(f"{settings.URL_PREFIX}/assets", StaticFiles(directory=str(ASSETS_DIR)), name="prefixed_assets")


    return app


# ---------------------------------------------------------------------------
# Module-level app instance (for uvicorn / gunicorn)
# ---------------------------------------------------------------------------
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=5000, reload=True)
