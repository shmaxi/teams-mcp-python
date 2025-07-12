"""Rate limiter for Microsoft Graph API."""

import asyncio
import time
from typing import TypeVar, Callable, Awaitable
from functools import wraps

T = TypeVar('T')


class RateLimiter:
    """Rate limiter with exponential backoff for 429 responses."""
    
    def __init__(self, requests_per_window: int = 10000, window_seconds: int = 600):
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait if necessary to respect rate limits."""
        async with self.lock:
            now = time.time()
            # Remove old requests outside the window
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < self.window_seconds]
            
            # Check if we're at the limit
            if len(self.requests) >= self.requests_per_window:
                # Wait until the oldest request is outside the window
                wait_time = self.window_seconds - (now - self.requests[0]) + 0.1
                await asyncio.sleep(wait_time)
                # Retry
                return await self.acquire()
            
            # Record this request
            self.requests.append(now)
    
    async def execute_with_retry(
        self,
        func: Callable[..., Awaitable[T]],
        *args,
        max_retries: int = 3,
        **kwargs
    ) -> T:
        """Execute function with rate limiting and exponential backoff."""
        last_error = None
        
        for attempt in range(max_retries):
            await self.acquire()
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Check if it's a rate limit error (429)
                if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                    if e.response.status_code == 429:
                        # Exponential backoff
                        wait_time = (2 ** attempt) * 1.0
                        retry_after = e.response.headers.get('Retry-After')
                        if retry_after:
                            wait_time = float(retry_after)
                        
                        await asyncio.sleep(wait_time)
                        last_error = e
                        continue
                
                # Not a rate limit error, re-raise
                raise
        
        # Max retries exceeded
        if last_error:
            raise last_error
        raise Exception("Max retries exceeded")