"""
Global asyncpg connection pool for high-performance database operations
"""
import os
import asyncpg
import logging
from typing import Optional
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class GlobalConnectionPool:
    """Global asyncpg connection pool with optimized settings"""
    
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self._dsn: Optional[str] = None
        
    async def initialize(self):
        """Initialize the connection pool"""
        if self._pool is not None:
            return
            
        # Get DSN and normalize for asyncpg
        dsn = os.getenv('DATABASE_URL')
        if dsn and dsn.startswith('postgresql+asyncpg://'):
            dsn = dsn.replace('postgresql+asyncpg://', 'postgresql://', 1)
        
        self._dsn = dsn
        
        try:
            self._pool = await asyncpg.create_pool(
                dsn=dsn,
                min_size=5,           # Minimum connections
                max_size=20,          # Maximum connections
                max_queries=50000,    # Max queries per connection
                max_inactive_connection_lifetime=300,  # 5 minutes
                command_timeout=5,    # 5 second command timeout
                statement_cache_size=0,  # Disable statement cache for pgbouncer
                server_settings={
                    'jit': 'off',
                    'statement_timeout': '5000',  # 5 second statement timeout
                    'idle_in_transaction_session_timeout': '5000',
                }
            )
            logger.info("Global connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    async def close(self):
        """Close the connection pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Global connection pool closed")
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool"""
        if self._pool is None:
            await self.initialize()
        
        async with self._pool.acquire() as conn:
            yield conn
    
    async def execute(self, query: str, *args, **kwargs):
        """Execute a query using the pool"""
        async with self.acquire() as conn:
            return await conn.execute(query, *args, **kwargs)
    
    async def fetch(self, query: str, *args, **kwargs):
        """Fetch multiple rows using the pool"""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args, **kwargs)
    
    async def fetchrow(self, query: str, *args, **kwargs):
        """Fetch a single row using the pool"""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args, **kwargs)
    
    async def fetchval(self, query: str, *args, **kwargs):
        """Fetch a single value using the pool"""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args, **kwargs)

# Global instance
global_pool = GlobalConnectionPool()
