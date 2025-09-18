"""
Performance monitoring middleware for automatic slow query detection and optimization
"""
import time
import logging
import asyncio
from fastapi import Request, Response
from typing import Callable
from config.security import SecurityConfig

logger = logging.getLogger(__name__)

class PerformanceMiddleware:
    """Middleware to monitor and log slow requests automatically"""
    
    def __init__(self, slow_threshold: float = None):
        self.slow_threshold = slow_threshold or SecurityConfig.SLOW_RESPONSE_THRESHOLD
        self.max_response_time = SecurityConfig.MAX_RESPONSE_TIME
        
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Monitor request performance and log slow requests"""
        start_time = time.time()
        
        try:
            # Process request with timeout protection
            response = await asyncio.wait_for(
                call_next(request), 
                timeout=self.max_response_time
            )
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            response.headers["X-Performance-Status"] = "OK"
            
            # Log slow requests with detailed information
            if response_time > self.slow_threshold:
                logger.warning(
                    f"SLOW REQUEST: {request.method} {request.url.path} "
                    f"took {response_time:.3f}s (threshold: {self.slow_threshold}s) "
                    f"- Status: {response.status_code} "
                    f"- Client: {request.client.host if request.client else 'unknown'}"
                )
                
                # Log query parameters for debugging
                if request.query_params:
                    logger.warning(f"Query params: {dict(request.query_params)}")
            
            # Log very fast requests for optimization tracking
            elif response_time < 0.1:
                logger.info(
                    f"FAST REQUEST: {request.method} {request.url.path} "
                    f"took {response_time:.3f}s - Status: {response.status_code}"
                )
            
            return response
            
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            logger.error(
                f"REQUEST TIMEOUT: {request.method} {request.url.path} "
                f"exceeded {self.max_response_time}s limit after {response_time:.3f}s"
            )
            
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=504,
                content={
                    "detail": f"Request timeout: Response time exceeded {self.max_response_time} seconds",
                    "error_code": "RESPONSE_TIMEOUT"
                },
                headers={
                    "X-Response-Time": f">{self.max_response_time}s",
                    "X-Performance-Status": "TIMEOUT"
                }
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(
                f"REQUEST ERROR: {request.method} {request.url.path} "
                f"failed after {response_time:.3f}s - Error: {str(e)}"
            )
            raise

# Global performance middleware instance
performance_middleware = PerformanceMiddleware()
