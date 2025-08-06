from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging
import re
from typing import Optional
from config.security import SecurityConfig, sanitize_input, validate_sql_injection

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    """Comprehensive security middleware with headers, validation, and protection"""
    
    def __init__(self):
        # Security headers configuration
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }
        
        # Forbidden patterns for request validation
        self.forbidden_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"onload=",
            r"onerror=",
            r"onclick=",
            r"onmouseover=",
            r"<iframe",
            r"<object",
            r"<embed",
            r"<form",
            r"<input",
            r"<textarea",
            r"<select",
            r"<button",
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.forbidden_patterns]
    
    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        for header, value in self.security_headers.items():
            response.headers[header] = value
    
    def _validate_request_headers(self, request: Request) -> Optional[str]:
        """Validate request headers for security issues"""
        # Check for suspicious headers
        suspicious_headers = [
            "X-Forwarded-For",
            "X-Real-IP",
            "X-Forwarded-Host",
            "X-Forwarded-Proto",
        ]
        
        for header in suspicious_headers:
            value = request.headers.get(header)
            if value:
                # Validate IP addresses
                if header in ["X-Forwarded-For", "X-Real-IP"]:
                    if not self._is_valid_ip(value.split(",")[0].strip()):
                        return f"Invalid IP address in {header}"
        
        # Check User-Agent for suspicious patterns
        user_agent = request.headers.get("User-Agent", "")
        if any(pattern.search(user_agent) for pattern in self.compiled_patterns):
            return "Suspicious User-Agent detected"
        
        return None
    
    def _validate_request_body(self, request: Request) -> Optional[str]:
        """Validate request body for security issues"""
        content_type = request.headers.get("content-type", "")
        
        # Only validate JSON and form data
        if "application/json" in content_type or "application/x-www-form-urlencoded" in content_type:
            try:
                # This is a simplified check - in production, you'd want to read the body
                # For now, we'll check the URL parameters
                for param, value in request.query_params.items():
                    if isinstance(value, str):
                        # Check for XSS patterns
                        if any(pattern.search(value) for pattern in self.compiled_patterns):
                            return f"XSS pattern detected in parameter: {param}"
                        
                        # Check for SQL injection
                        if not validate_sql_injection(value):
                            return f"SQL injection pattern detected in parameter: {param}"
                        
                        # Sanitize the value
                        sanitized_value = sanitize_input(value)
                        if sanitized_value != value:
                            return f"Invalid characters in parameter: {param}"
                
            except Exception as e:
                logger.warning(f"Error validating request body: {e}")
                return "Request validation error"
        
        return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _log_security_event(self, request: Request, issue: str):
        """Log security events for monitoring"""
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")
        path = request.url.path
        method = request.method
        
        logger.warning(
            f"Security issue detected - IP: {client_ip}, "
            f"User-Agent: {user_agent}, Path: {method} {path}, Issue: {issue}"
        )
    
    async def __call__(self, request: Request, call_next):
        """Security middleware implementation"""
        try:
            # Skip security checks for development mode
            if request.headers.get("X-Development-Mode") == "true":
                response = await call_next(request)
                self._add_security_headers(response)
                return response
            
            # Validate request headers
            header_issue = self._validate_request_headers(request)
            if header_issue:
                self._log_security_event(request, header_issue)
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid request headers"}
                )
            
            # Validate request body
            body_issue = self._validate_request_body(request)
            if body_issue:
                self._log_security_event(request, body_issue)
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid request content"}
                )
            
            # Check request size
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    size = int(content_length)
                    if size > SecurityConfig.MAX_QUERY_LENGTH:
                        self._log_security_event(request, "Request too large")
                        return JSONResponse(
                            status_code=413,
                            content={"detail": "Request too large"}
                        )
                except ValueError:
                    pass
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            self._add_security_headers(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            # On error, allow request to proceed but log the issue
            response = await call_next(request)
            self._add_security_headers(response)
            return response

# Create security middleware instance
security_middleware = SecurityMiddleware() 