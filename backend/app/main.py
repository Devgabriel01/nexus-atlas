from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import get_settings
from app.database import init_db
from app.middleware.rate_limit import RateLimitMiddleware
from app.utils.logger import logger
from app.routers import (
    auth, scan, anomalies, reports, exploration, history, analyze,
    integrations, ws, organizations, billing,
)
# Touch models so SQLAlchemy registers them before init_db()
from app.models import organization as _org  # noqa: F401

settings = get_settings()

# Expose GEE settings to os.environ so the geospatial module (which reads os.environ) can find them
import os as _os
if settings.GEE_PROJECT:
    _os.environ["GEE_PROJECT"] = settings.GEE_PROJECT
if settings.GEE_SERVICE_ACCOUNT:
    _os.environ["GEE_SERVICE_ACCOUNT"] = settings.GEE_SERVICE_ACCOUNT
if settings.GEE_KEY_FILE:
    _os.environ["GEE_KEY_FILE"] = settings.GEE_KEY_FILE

Path("./scans").mkdir(exist_ok=True)
Path("./reports").mkdir(exist_ok=True)
Path("./logs").mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("NEXUS ATLAS backend starting...")
    await init_db()
    logger.info("Database initialized.")
    yield
    logger.info("NEXUS ATLAS backend shutting down.")


app = FastAPI(
    title="NEXUS ATLAS API",
    description="Advanced Geospatial Intelligence Platform",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

# Routers
app.include_router(auth.router)
app.include_router(scan.router)
app.include_router(anomalies.router)
app.include_router(reports.router)
app.include_router(exploration.router)
app.include_router(history.router)
app.include_router(analyze.router)
app.include_router(integrations.router)
app.include_router(ws.router)
app.include_router(organizations.router)
app.include_router(billing.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "system": "NEXUS ATLAS",
        "status": "ONLINE",
        "version": settings.APP_VERSION,
        "modules": ["scan", "anomalies", "reports", "exploration", "history", "analyze"],
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "system": "NEXUS ATLAS"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
