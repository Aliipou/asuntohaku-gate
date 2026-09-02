"""FastAPI application.

Assembled here and mounted by ``api/index.py`` on Vercel, or run locally with
``uvicorn api.app.main:app --reload``.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.app import cache
from api.app.routers import admin, applications, units, viewings

app = FastAPI(
    title="asuntohaku-gate",
    version="0.1.0",
    description=(
        "Housing search and application demo. All data is synthetic and every income, "
        "wealth and rent-ratio threshold is invented for the demo; none of them is a "
        "current statutory figure. There is no authentication."
    ),
)

# The frontend is deployed as a separate origin in development. Locked to the
# local dev server plus whatever the deployment sets; not open to the world.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+|https://.*\.vercel\.app",
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(units.router)
app.include_router(applications.router)
app.include_router(viewings.router)
app.include_router(admin.router)


@app.get("/api/health", tags=["meta"])
def health() -> dict[str, object]:
    """Says what is actually wired up, including when the cache is not."""
    return {"status": "ok", "cache": "redis" if cache.cache_enabled() else "disabled"}
