# Today's date: 25/07/2025
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging
import os

from config.database import init_db
from config.logging import setup_logging, log_api_request, log_security_event
from middleware.rate_limiter import rate_limiter, rate_limiting_middleware
from middleware.security import security_middleware
from middleware.timeout_middleware import timeout_middleware
from api.routers import auth, candidates, jobs, applications, recommendations, interactions, analytics, system, search, gdpr, recruiter
from services.api_service import api_service
from services.cache_service import cache_service
from services.faiss_service import faiss_service

# Setup logging
loggers = setup_logging()
logger = loggers["api"]

# Note: File size limit is configured via uvicorn command line arguments
# Use: uvicorn api.main:app --host 0.0.0.0 --port 8000 --limit-request-line 0 --limit-request-field_size 0 --limit-request-fields 0

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting application...")
    try:
        # Initialize cache service
        await cache_service.connect()
        logger.info("Cache service initialized successfully")
        # Temporarily disable FAISS warmup to avoid prepared statement issues
        logger.info("FAISS warmup disabled during startup to avoid prepared statement conflicts")
        # TODO: Re-enable FAISS warmup once prepared statement issues are resolved
        # try:
        #     from config.database import get_db_session
        #     # Create a short-lived session to warm the index
        #     async for session in get_db_session():
        #         # Build/load in background without failing startup
        #         await faiss_service.ensure_jobs_index(session)
        #         break
        # except Exception as e:
        #     logger.warning(f"FAISS warmup skipped: {e}")
        
        # Temporarily skip database initialization to avoid prepared statement issues
        logger.info("Skipping database initialization for now...")
        # from config.database import check_database_connection
        # connection_ok = await check_database_connection()
        # if connection_ok:
        #     logger.info("Database connection verified successfully")
        # else:
        #     logger.warning("Database connection check failed, but continuing...")
    except Exception as e:
        logger.error(f"Failed to check database connection: {e}")
        # Don't raise the exception, just log it and continue
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await cache_service.disconnect()

# Create FastAPI app with security features
app = FastAPI(
    title="CV Matcher API",
    description="Advanced job matching platform with comprehensive security",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware with comprehensive origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001", 
        "http://localhost:8000", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8000",
        "https://yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
)

# Add security middleware
@app.middleware("http")
async def security_middleware_handler(request: Request, call_next):
    return await security_middleware(request, call_next)

# Add timeout middleware (should be first to catch slow requests early)
@app.middleware("http")
async def timeout_middleware_handler(request: Request, call_next):
    return await timeout_middleware(request, call_next)

# Add rate limiting middleware
@app.middleware("http")
async def rate_limiting_middleware_handler(request: Request, call_next):
    return await rate_limiting_middleware(request, call_next)

# Add request logging middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Log response time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log request and response
    log_api_request(request, response, process_time)
    
    # Log security events if needed
    if response.status_code >= 400:
        log_security_event(request, f"HTTP {response.status_code}")
    
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    log_security_event(request, f"Unhandled exception: {type(exc).__name__}")
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Include routers with proper prefixes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(candidates.router, prefix="/api/v1/candidates", tags=["Candidates"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(applications.router, prefix="/api/v1/applications", tags=["Applications"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["Recommendations"])
app.include_router(interactions.router, prefix="/api/v1/interactions", tags=["Interactions"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(system.router, prefix="/api/v1/system", tags=["System"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(gdpr.router, prefix="/api/v1/gdpr", tags=["GDPR"])
app.include_router(recruiter.router, prefix="/api/v1/recruiter", tags=["Recruiter"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "2.0.0"
    }

@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics"""
    try:
        stats = await cache_service.get_cache_stats()
        return {
            "cache_stats": stats,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {
            "cache_stats": {},
            "status": "error",
            "error": str(e)
        }

# Security status endpoint
@app.get("/security/status")
async def security_status(request: Request):
    """Security status endpoint"""
    return {
        "security_enabled": True,
        "rate_limiting": True,
        "cors_enabled": True,
        "request_id": request.headers.get("X-Request-ID", "unknown")
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "CV Matcher API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }
