"""
X Algorithm Tweet Generator API
FastAPI backend for tweet generation, analysis, and scheduling.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

from app.api.v1 import tweets, profiles, threads, scheduling, analytics, ab_tests, style
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Scheduler for background tasks
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting X Tweet Generator API...")
    scheduler.start()
    logger.info("Scheduler started")

    yield

    # Shutdown
    logger.info("Shutting down...")
    scheduler.shutdown()
    logger.info("Scheduler stopped")


# Create FastAPI app
app = FastAPI(
    title="X Tweet Generator API",
    description="AI-powered tweet generation and optimization using X's algorithm",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "x-tweet-generator-api"}


# Include routers
app.include_router(
    tweets.router,
    prefix="/api/v1/tweets",
    tags=["tweets"]
)

app.include_router(
    profiles.router,
    prefix="/api/v1/profiles",
    tags=["profiles"]
)

app.include_router(
    threads.router,
    prefix="/api/v1/threads",
    tags=["threads"]
)

app.include_router(
    scheduling.router,
    prefix="/api/v1/scheduling",
    tags=["scheduling"]
)

app.include_router(
    analytics.router,
    prefix="/api/v1/analytics",
    tags=["analytics"]
)

app.include_router(
    ab_tests.router,
    prefix="/api/v1/ab",
    tags=["ab_tests"]
)

app.include_router(
    style.router,
    prefix="/api/v1/style",
    tags=["style"]
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "X Tweet Generator API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
