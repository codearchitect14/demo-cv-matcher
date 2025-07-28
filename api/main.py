# Today's date: 25/07/2025
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from config.database import init_db
from api.routers import auth, candidates, jobs, applications, recommendations, interactions, analytics, system, search

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting up Job Recommendation System...")
    await init_db()
    logger.info("Database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Job Recommendation System...")

# Create FastAPI app
app = FastAPI(
    title="Job Recommendation System API",
    description="Intelligent job recommendation system with semantic search and personalization",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(candidates.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(applications.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(interactions.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Job Recommendation System API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "job-recommendation-system",
        "timestamp": "2024-01-01T00:00:00Z"
    }

# API info endpoint
@app.get("/api/v1/info")
async def api_info():
    """API information endpoint"""
    return {
        "name": "Job Recommendation System API",
        "version": "1.0.0",
        "description": "Intelligent job recommendation system with semantic search and personalization",
        "features": [
            "Authentication & User Management",
            "Candidate Profile Management",
            "Job Posting Management",
            "Application Management",
            "Semantic Search & Recommendations",
            "Interaction Tracking",
            "Personalization & ML",
            "Analytics & Insights",
            "System Management"
        ],
        "endpoints": {
            "auth": "/api/v1/auth",
            "candidates": "/api/v1/candidates",
            "jobs": "/api/v1/jobs",
            "applications": "/api/v1/applications",
            "recommendations": "/api/v1/recommendations",
            "interactions": "/api/v1/interactions",
            "analytics": "/api/v1/analytics",
            "system": "/api/v1/system",
            "search": "/api/v1/search"
        }
    }
