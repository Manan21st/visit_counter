from typing import Dict, List, Any
import asyncio
from datetime import datetime
from ..core.redis_manager import RedisManager

class VisitCounterService:
    # Creating class attributes so all instances share the same dict and lock
    lock = asyncio.Lock()
    cache : Dict[str, Dict[str, Any]] = {}
    CACHE_TTL = 5 # Five sec TTL for cache

    def __init__(self):
        """Initialize the visit counter service with Redis manager"""
        self.redis_manager = RedisManager()

    async def increment_visit(self, page_id: str) -> None:
        """
        Increment visit count for a page
        
        Args:
            page_id: Unique identifier for the page
        """
        # TODO: Implement visit count increment
        async with self.lock:
            count = await self.redis_manager.increment(page_id,1)

            self.cache[page_id] = {"count": count, "last_updated": datetime.now()}

            return count


    async def get_visit_count(self, page_id: str) -> int:
        """
        Get current visit count for a page
        
        Args:
            page_id: Unique identifier for the page
            
        Returns:
            Current visit count
        """
        # TODO: Implement getting visit count
        async with self.lock:
            curr_time = datetime.now()
            # Check if the page_id is in cache and the cache is still valid
            if page_id in self.cache and (curr_time - self.cache[page_id]["last_updated"]).seconds < self.CACHE_TTL:
                return self.cache[page_id]["count"], "cache"
            count = await self.redis_manager.get(page_id)

            self.cache[page_id] = {"count": count, "last_updated": curr_time} if count else {"count": 0, "last_updated": curr_time}
            return count, "redis"
