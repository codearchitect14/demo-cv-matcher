import os
import logging
import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from sendgrid.helpers.mail import Email as SendGridEmail
from dotenv import load_dotenv
from functools import lru_cache
import time

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class EmailTemplateCache:
    """Template cache for email templates with TTL support"""
    
    def __init__(self, ttl_minutes: int = 60):
        self.cache = {}
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def _get_cache_key(self, template_name: str, **kwargs) -> str:
        """Generate cache key based on template name and parameters"""
        params_str = json.dumps(kwargs, sort_keys=True)
        return hashlib.md5(f"{template_name}:{params_str}".encode()).hexdigest()
    
    def get(self, template_name: str, **kwargs) -> Optional[str]:
        """Get cached template"""
        cache_key = self._get_cache_key(template_name, **kwargs)
        if cache_key in self.cache:
            cached_time, content = self.cache[cache_key]
            if datetime.now() - cached_time < self.ttl:
                logger.debug(f"Template cache hit for {template_name}")
                return content
            else:
                # Cache expired
                del self.cache[cache_key]
        return None
    
    def set(self, template_name: str, content: str, **kwargs) -> None:
        """Set template in cache"""
        cache_key = self._get_cache_key(template_name, **kwargs)
        self.cache[cache_key] = (datetime.now(), content)
        logger.debug(f"Template cached for {template_name}")
    
    def clear(self) -> None:
        """Clear all cached templates"""
        self.cache.clear()
        logger.info("Email template cache cleared")

class EmailBatch:
    """Batch email sending for better performance"""
    
    def __init__(self, max_batch_size: int = 10, batch_timeout: float = 5.0):
        self.max_batch_size = max_batch_size
        self.batch_timeout = batch_timeout
        self.pending_emails = []
        self.batch_task = None
        self._lock = asyncio.Lock()
    
    async def add_email(self, to_email: str, subject: str, html_content: str, 
                       from_email: Optional[str] = None, priority: str = "normal") -> None:
        """Add email to batch"""
        async with self._lock:
            email_data = {
                "to_email": to_email,
                "subject": subject,
                "html_content": html_content,
                "from_email": from_email,
                "priority": priority,
                "timestamp": datetime.now()
            }
            
            # Prioritize high priority emails
            if priority == "high":
                self.pending_emails.insert(0, email_data)
            else:
                self.pending_emails.append(email_data)
            
            # Start batch processing if not already running
            if self.batch_task is None or self.batch_task.done():
                self.batch_task = asyncio.create_task(self._process_batch())
    
    async def _process_batch(self) -> None:
        """Process email batch"""
        try:
            while True:
                await asyncio.sleep(0.1)  # Small delay to collect more emails
                
                async with self._lock:
                    if not self.pending_emails:
                        break
                    
                    # Take up to max_batch_size emails
                    batch_emails = self.pending_emails[:self.max_batch_size]
                    self.pending_emails = self.pending_emails[self.max_batch_size:]
                
                if batch_emails:
                    await self._send_batch(batch_emails)
                
                # Check if we should continue (more emails or timeout)
                async with self._lock:
                    if not self.pending_emails:
                        break
                
        except Exception as e:
            logger.error(f"Error processing email batch: {e}")
    
    async def _send_batch(self, emails: List[Dict]) -> None:
        """Send batch of emails concurrently"""
        if not emails:
            return
        
        logger.info(f"Sending batch of {len(emails)} emails")
        
        # Send emails concurrently
        tasks = []
        for email_data in emails:
            task = asyncio.create_task(
                self._send_single_email(
                    email_data["to_email"],
                    email_data["subject"],
                    email_data["html_content"],
                    email_data["from_email"]
                )
            )
            tasks.append(task)
        
        # Wait for all emails to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log results
        success_count = sum(1 for result in results if result is True)
        error_count = len(results) - success_count
        
        logger.info(f"Batch email results: {success_count} successful, {error_count} failed")
    
    async def _send_single_email(self, to_email: str, subject: str, 
                                html_content: str, from_email: Optional[str] = None) -> bool:
        """Send single email (placeholder - will be implemented by EnhancedEmailService)"""
        # This will be overridden by the main service
        return True

class EnhancedEmailService:
    """Enhanced email service with caching, batching, and error handling"""
    
    def __init__(self):
        """Initialize enhanced email service"""
        self.api_key = os.getenv("SENDGRID_API_KEY")
        if not self.api_key:
            raise ValueError("SENDGRID_API_KEY not found in environment variables")
        
        self.sg = SendGridAPIClient(api_key=self.api_key)
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "ali.mughal@boolmind.com")
        
        # Initialize cache and batch processor
        self.template_cache = EmailTemplateCache(ttl_minutes=60)
        self.email_batch = EmailBatch(max_batch_size=10, batch_timeout=5.0)
        
        # Error handling configuration
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        self.circuit_breaker_threshold = 5  # failures before circuit breaker opens
        self.circuit_breaker_timeout = 60  # seconds
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_breaker_open = False
        
        logger.info("Enhanced Email Service initialized")
    
    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open"""
        if not self.circuit_breaker_open:
            return False
        
        # Check if timeout has passed
        if (self.last_failure_time and 
            datetime.now() - self.last_failure_time > timedelta(seconds=self.circuit_breaker_timeout)):
            self.circuit_breaker_open = False
            self.failure_count = 0
            logger.info("Circuit breaker reset - attempting to send emails again")
            return False
        
        return True
    
    def _record_success(self) -> None:
        """Record successful email send"""
        self.failure_count = 0
        self.circuit_breaker_open = False
    
    def _record_failure(self) -> None:
        """Record failed email send"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.circuit_breaker_threshold:
            self.circuit_breaker_open = True
            logger.error(f"Circuit breaker opened after {self.failure_count} failures")
    
    async def send_email_async(self, to_email: str, subject: str, html_content: str,
                              from_email: Optional[str] = None, priority: str = "normal",
                              use_batch: bool = True) -> bool:
        """
        Send email asynchronously with enhanced error handling
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            from_email: Sender email (optional)
            priority: Email priority ("high", "normal", "low")
            use_batch: Whether to use batch processing
            
        Returns:
            bool: True if email queued/sent successfully
        """
        try:
            # Check circuit breaker
            if self._is_circuit_breaker_open():
                logger.warning("Circuit breaker is open - email queued for later")
                # Queue email for later when circuit breaker resets
                await self.email_batch.add_email(to_email, subject, html_content, from_email, priority)
                return True
            
            if use_batch and priority != "high":
                # Add to batch for processing
                await self.email_batch.add_email(to_email, subject, html_content, from_email, priority)
                logger.info(f"Email queued for batch sending to {to_email}")
                return True
            else:
                # Send immediately for high priority emails
                return await self._send_email_with_retry(to_email, subject, html_content, from_email)
                
        except Exception as e:
            logger.error(f"Error in send_email_async: {e}")
            self._record_failure()
            return False
    
    async def _send_email_with_retry(self, to_email: str, subject: str, html_content: str,
                                    from_email: Optional[str] = None) -> bool:
        """Send email with retry logic"""
        sender_email = from_email or self.from_email
        
        for attempt in range(self.max_retries):
            try:
                message = Mail(
                    from_email=sender_email,
                    to_emails=to_email,
                    subject=subject,
                    html_content=html_content
                )
                
                # Send email with timeout
                response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, self.sg.send, message
                    ),
                    timeout=10.0
                )
                
                if response.status_code in [200, 201, 202]:
                    logger.info(f"Email sent successfully to {to_email}")
                    self._record_success()
                    return True
                else:
                    logger.warning(f"SendGrid returned status {response.status_code} for {to_email}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                        continue
                    else:
                        self._record_failure()
                        return False
                        
            except asyncio.TimeoutError:
                logger.error(f"Email send timeout for {to_email} (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    self._record_failure()
                    return False
                    
            except Exception as e:
                logger.error(f"Email send error for {to_email} (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    self._record_failure()
                    return False
        
        return False
    
    def get_template(self, template_name: str, **kwargs) -> Optional[str]:
        """Get cached template or generate new one"""
        # Try cache first
        cached_template = self.template_cache.get(template_name, **kwargs)
        if cached_template:
            return cached_template
        
        # Generate template based on name
        template = self._generate_template(template_name, **kwargs)
        if template:
            self.template_cache.set(template_name, template, **kwargs)
        
        return template
    
    def _generate_template(self, template_name: str, **kwargs) -> Optional[str]:
        """Generate email template based on name and parameters"""
        try:
            from services.email_templates import get_template
            return get_template(template_name, **kwargs)
        except Exception as e:
            logger.error(f"Error generating template {template_name}: {e}")
            return None
    
    async def send_template_email(self, template_name: str, to_email: str, 
                                 subject: str, priority: str = "normal", **kwargs) -> bool:
        """Send email using cached template"""
        try:
            # Remove priority and other non-template parameters from kwargs
            template_kwargs = {k: v for k, v in kwargs.items() 
                             if k not in ['priority', 'use_batch', 'from_email']}
            
            # Get template from cache or generate
            template = self.get_template(template_name, **template_kwargs)
            if not template:
                logger.error(f"Template {template_name} not found")
                return False
            
            # Send email - only pass email-specific parameters
            email_kwargs = {k: v for k, v in kwargs.items() 
                           if k in ['from_email', 'use_batch']}
            return await self.send_email_async(to_email, subject, template, 
                                             priority=priority, **email_kwargs)
            
        except Exception as e:
            logger.error(f"Error sending template email {template_name}: {e}")
            return False
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "circuit_breaker_open": self.circuit_breaker_open,
            "failure_count": self.failure_count,
            "cached_templates": len(self.template_cache.cache),
            "pending_emails": len(self.email_batch.pending_emails),
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None
        }

# Global instance
enhanced_email_service = EnhancedEmailService()
