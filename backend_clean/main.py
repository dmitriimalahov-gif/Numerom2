"""
Main Application Entry Point

FastAPI application initialization and configuration

Date created: 2025-10-09
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from core.config import settings
from database.connection import Database, get_database
from api.v1 import (
    auth_router,
    credit_router,
    payment_router,
    numerology_router,
    lesson_router,
    consultation_router,
    user_router,
    admin_router,
    charts_router,
    vedic_time_router,
    quiz_router,
    learning_router,
    reports_router
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Numerom API",
    description="Self-Knowledge Through Numbers - Numerology Platform API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on settings.ALLOWED_ORIGINS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===========================================
# Lifecycle Events
# ===========================================

@app.on_event("startup")
async def startup_event():
    """
    Startup event handler

    Connects to database and initializes super admin
    """
    logger.info("Starting Numerom API...")

    # Connect to database
    try:
        from database.connection import database
        await database.connect()
        logger.info(f"✅ Connected to MongoDB: {settings.MONGODB_DATABASE}")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise

    # Ensure super admin exists
    try:
        from services.auth_service import AuthService
        from database.repositories.user_repository import UserRepository
        from database.connection import database

        db = database.get_database()
        user_repo = UserRepository(db)
        auth_service = AuthService(user_repo)

        await auth_service.ensure_super_admin_exists()
        logger.info("✅ Super admin check completed")
    except Exception as e:
        logger.error(f"⚠️  Super admin check failed: {e}")

    logger.info("🚀 Numerom API is ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler

    Closes database connections
    """
    logger.info("Shutting down Numerom API...")

    try:
        from database.connection import database
        await database.disconnect()
        logger.info("✅ Disconnected from MongoDB")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

    logger.info("👋 Numerom API shutdown complete")


# ===========================================
# Root Endpoint
# ===========================================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API status
    """
    return {
        "message": "NUMEROM API - Self-Knowledge Through Numbers",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    """
    try:
        # Check database connection
        db = await get_database()
        await db.command('ping')

        return {
            "status": "healthy",
            "database": "connected",
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


# ===========================================
# Include Routers
# ===========================================

# API prefix (keep /api for backward compatibility with frontend)
API_PREFIX = "/api"

# Authentication & Authorization
app.include_router(auth_router, prefix=API_PREFIX)

# User Profile
app.include_router(user_router, prefix=API_PREFIX)

# Credits & Payments
app.include_router(credit_router, prefix=API_PREFIX)
app.include_router(payment_router, prefix=API_PREFIX)

# Core Features
app.include_router(numerology_router, prefix=API_PREFIX)
app.include_router(lesson_router, prefix=API_PREFIX)
app.include_router(consultation_router, prefix=API_PREFIX)
app.include_router(charts_router, prefix=API_PREFIX)
app.include_router(vedic_time_router, prefix=API_PREFIX)
app.include_router(quiz_router, prefix=API_PREFIX)
app.include_router(learning_router, prefix=API_PREFIX)
app.include_router(reports_router, prefix=API_PREFIX)

# Admin Operations
app.include_router(admin_router, prefix=API_PREFIX)

logger.info("✅ All routers registered")


# ===========================================
# Run Application
# ===========================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
