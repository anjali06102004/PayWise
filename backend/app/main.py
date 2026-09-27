from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging import setup_logging
from app.core.rate_limit import rate_limit_middleware
from app.core.observability import observability
from app.api.v1 import auth, expenses, financial, ai, decision
import logging

# Setup structured logging
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Personal Spending Agent API",
    description="API for personal financial decision assistant",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(expenses.router, prefix="/api/v1")
app.include_router(financial.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(decision.router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    logger.info("Starting up PayWise API")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down PayWise API")
    observability.flush()
    logger.info("Observability flushed")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Personal Spending Agent API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Enhanced health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "observability_enabled": observability.enabled,
        "llm_provider": settings.LLM_PROVIDER,
        "jev_enabled": bool(settings.JEV_API_KEY)
    }
