import asyncio
import time
import logging
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Callable
from config.security import SecurityConfig

logger = logging.getLogger(__name__)

class TimeoutMiddleware:
    """Middleware to enforce maximum response time limits"""
    
    def __init__(self, max_response_time: float = None):
        """
        Initialize timeout middleware
        
        Args:
            max_response_time: Maximum allowed response time in seconds (default: from config)
        """
        self.max_response_time = max_response_time or SecurityConfig.MAX_RESPONSE_TIME
        self.slow_response_threshold = SecurityConfig.SLOW_RESPONSE_THRESHOLD
        logger.info(f"Timeout middleware initialized with {self.max_response_time}s limit")
    
    async def __call__(self, request: Request, call_next: Callable) -> JSONResponse:
        """Enforce response time limit"""
        start_time = time.time()
        
        try:
            # Create a timeout task
            response_task = asyncio.create_task(call_next(request))
            
            # Wait for either completion or timeout
            try:
                response = await asyncio.wait_for(response_task, timeout=self.max_response_time)
                
                # Calculate actual response time
                response_time = time.time() - start_time
                
                # Add response time header
                response.headers["X-Response-Time"] = f"{response_time:.3f}s"
                
                # Log slow responses (but still successful)
                if response_time > self.slow_response_threshold:
                    logger.warning(
                        f"Slow response detected: {request.method} {request.url.path} "
                        f"took {response_time:.3f}s (threshold: {self.slow_response_threshold}s, limit: {self.max_response_time}s)"
                    )
                
                return response
                
            except asyncio.TimeoutError:
                # Cancel the original task
                response_task.cancel()
                
                # Log the timeout
                logger.error(
                    f"Request timeout: {request.method} {request.url.path} "
                    f"exceeded {self.max_response_time}s limit"
                )
                
                # Return timeout response
                return JSONResponse(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    content={
                        "detail": f"Request timeout: Response time exceeded {self.max_response_time} seconds",
                        "error_code": "RESPONSE_TIMEOUT",
                        "max_response_time": self.max_response_time
                    },
                    headers={
                        "X-Response-Time": f">{self.max_response_time}s",
                        "X-Timeout-Limit": str(self.max_response_time)
                    }
                )
                
        except Exception as e:
            logger.error(f"Timeout middleware error: {e}")
            # If there's an error in the middleware, let the request proceed
            return await call_next(request)

# Create timeout middleware instance
timeout_middleware = TimeoutMiddleware()
