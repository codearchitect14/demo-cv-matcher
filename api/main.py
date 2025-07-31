# Today's date: 25/07/2025
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging

from config.database import init_db
from config.logging import setup_logging, log_api_request, log_security_event
from middleware.rate_limiter import rate_limiter
from api.routers import auth, candidates, jobs, applications, recommendations, interactions, analytics, system, search, gdpr
from services.api_service import api_service

# Setup logging
loggers = setup_logging()
logger = loggers["api"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting up Job Recommendation System...")
    try:
        # Skip table creation during startup to avoid prepared statement issues
        # Tables should already exist from previous runs
        logger.info("Skipping table creation - assuming tables exist")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        # Don't fail startup, just log the error
    
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

# Add rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    return await rate_limiter(request, call_next)

# Add request logging middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    """Log all API requests"""
    start_time = time.time()
    
    # Log request
    request_data = {
        "method": request.method,
        "path": str(request.url.path),
        "client_ip": request.client.host,
        "user_agent": request.headers.get("user-agent", "")
    }
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Log response
        response_data = {
            "status_code": response.status_code,
            "duration": duration
        }
        
        log_api_request(request_data, response_data, duration)
        
        # Log security events for certain status codes
        if response.status_code in [401, 403, 429]:
            log_security_event("Unauthorized Access", {
                "ip": request.client.host,
                "path": str(request.url.path),
                "status_code": response.status_code
            })
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Request failed: {request_data} - Error: {str(e)}")
        
        # Log security event for exceptions
        log_security_event("Request Exception", {
            "ip": request.client.host,
            "path": str(request.url.path),
            "error": str(e)
        })
        
        raise

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
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
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
app.include_router(gdpr.router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    logger.info("Root endpoint accessed")
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
    logger.info("Health check endpoint accessed")
    return {
        "status": "healthy",
        "service": "job-recommendation-system",
        "timestamp": "2024-01-01T00:00:00Z"
    }

# API info endpoint
@app.get("/api/v1/info")
async def api_info():
    """API information endpoint"""
    logger.info("API info endpoint accessed")
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
