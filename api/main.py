"""
FastAPI application factory for the Playbooks platform.

Mounts all API routers under /api/v1, the legacy backward-compatible
router at /, static files, CORS middleware, and the APScheduler lifespan.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from api.config import settings

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

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(catalog_router, prefix="/api/v1")
    app.include_router(payments_router, prefix="/api/v1")
    app.include_router(subscribe_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")

    # --- Legacy backward-compatible router (serves existing HTML pages) ---
    from api.routers.legacy import router as legacy_router
    app.include_router(legacy_router)

    # --- Static files ---
    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    if ASSETS_DIR.is_dir():
        app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

    # --- URL_PREFIX middleware (for subpath deployment like /playbooks) ---
    # Strips the prefix from incoming request paths AND rewrites HTML links
    # so the app works behind a reverse proxy that adds a path prefix.
    if settings.URL_PREFIX:
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.requests import Request
        from starlette.responses import Response

        class URLPrefixMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next):
                # Strip prefix from incoming path so routes match
                prefix = settings.URL_PREFIX
                path = request.scope.get("path", "")
                if path.startswith(prefix + "/"):
                    request.scope["path"] = path[len(prefix):]
                elif path == prefix:
                    request.scope["path"] = "/"

                response: Response = await call_next(request)

                # Rewrite links in HTML responses to include the prefix
                if response.headers.get("content-type", "").startswith("text/html"):
                    body = b""
                    async for chunk in response.body_iterator:
                        if isinstance(chunk, str):
                            body += chunk.encode()
                        else:
                            body += chunk
                    text = body.decode()
                    text = text.replace('href="/', f'href="{prefix}/')
                    text = text.replace("href='/", f"href='{prefix}/")
                    text = text.replace('src="/', f'src="{prefix}/')
                    text = text.replace("src='/", f"src='{prefix}/")
                    text = text.replace('action="/', f'action="{prefix}/')
                    text = text.replace("action='/", f"action='{prefix}/")
                    return HTMLResponse(content=text, status_code=response.status_code,
                                        headers=dict(response.headers))
                return response

        app.add_middleware(URLPrefixMiddleware)

    return app


# ---------------------------------------------------------------------------
# Module-level app instance (for uvicorn / gunicorn)
# ---------------------------------------------------------------------------
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=5000, reload=True)
