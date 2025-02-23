from typing import Dict, List, Any
import asyncio
from datetime import datetime
from ..core.redis_manager import RedisManager

class VisitCounterService:
    # Creating class attributes so all instances share the same dict and lock
    lock = asyncio.Lock()
    cache : Dict[str, Dict[str, Any]] = {}
    CACHE_TTL = 5 # Five sec TTL for cache
    buffer : Dict[str, int] = {}
    FLUSH_INTERVAL = 30 # Thirty sec interval to flush cache to Redis

    def __init__(self):
        """Initialize the visit counter service with Redis manager"""
        self.redis_manager = RedisManager()
        asyncio.create_task(self._flush_to_redis())

    async def increment_visit(self, page_id: str) -> None:
        """
        Increment visit count for a page
        
        Args:
            page_id: Unique identifier for the page
        """
        # TODO: Implement visit count increment
        async with self.lock:
            if page_id not in self.buffer:
                self.buffer[page_id] = 0

            self.buffer[page_id] += 1


    async def get_visit_count(self, page_id: str) -> Dict[str, Any]:
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
                count = self.cache[page_id]["count"]
                source = "cache"
            else:
                persisted_count = await self.redis_manager.get(page_id)
                source = "redis"
                if persisted_count is None:
                    persisted_count = 0
                self.cache[page_id] = {"count": persisted_count, "last_updated": curr_time} # Update cache
                count = persisted_count


            pending_count = self.buffer.get(page_id, 0)
            total_count = count + pending_count
            return {"visits": total_count, "served_via": source}

    async def _flush_to_redis(self):
        while True:
            await asyncio.sleep(self.FLUSH_INTERVAL)
            async with self.lock:
                if not self.buffer:
                    continue

                copy_buffer = self.buffer.copy()
                self.buffer.clear()
            tasks = [self.redis_manager.increment(page_id, count) for page_id, count in copy_buffer.items() if count > 0]
            if tasks:
                await asyncio.gather(*tasks)    

visit_counter_service = VisitCounterService()
