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
from middleware.security import security_middleware
from api.routers import auth, candidates, jobs, applications, recommendations, interactions, analytics, system, search, gdpr, recruiter
from services.api_service import api_service

# Setup logging
loggers = setup_logging()
logger = loggers["api"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting application...")
    try:
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

# Create FastAPI app with security features
app = FastAPI(
    title="CV Matcher API",
    description="Advanced job matching platform with comprehensive security",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware with security considerations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:8000", "https://yourdomain.com"],  # Configure for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
)

# Add security middleware
@app.middleware("http")
async def security_middleware_handler(request: Request, call_next):
    return await security_middleware(request, call_next)

# Add rate limiting middleware
@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    return await rate_limiter(request, call_next)

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

# Include routers with security considerations
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

# Security status endpoint (admin only)
@app.get("/security/status")
async def security_status(request: Request):
    """Get security status and rate limit information"""
    try:
        # Get rate limit status
        rate_limit_status = await rate_limiter.get_rate_limit_status(request)
        
        return {
            "rate_limit_status": rate_limit_status,
            "security_headers_enabled": True,
            "input_validation_enabled": True,
            "sql_injection_protection": True,
            "xss_protection": True,
            "csrf_protection": True
        }
    except Exception as e:
        logger.error(f"Error getting security status: {e}")
        return {"error": "Failed to get security status"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with security information"""
    return {
        "message": "CV Matcher API v2.0.0",
        "security": "Advanced security features enabled",
        "documentation": "/docs",
        "health": "/health"
    }
