from typing import Dict, Any
import asyncio
from datetime import datetime, timedelta
from ..core.redis_manager import RedisManager

class VisitCounterService:
    # Creating class attributes so all instances share the same dict and lock    
    CACHE_TTL = 5  # Five sec TTL for cache
    FLUSH_INTERVAL = 30  # Thirty sec interval to flush cache to Redis

    def __init__(self, redis_manager: RedisManager):
        """Initialize the visit counter service with Redis manager"""
        self.redis_manager = redis_manager
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_locks: Dict[str, asyncio.Lock] = {}

        self.write_buffer: Dict[str, int] = {}
        self.buffer_locks: Dict[str, asyncio.Lock] = {}

        asyncio.create_task(self.flush_buffer())

    async def flush_buffer(self) -> None:
        """Flush the write buffer to Redis"""
        while True:
            await asyncio.sleep(self.FLUSH_INTERVAL)
            for page_id in list(self.write_buffer.keys()):
                await self.flush_buffer_key(page_id)

    async def flush_buffer_key(self, page_id: str) -> None:
        """Flush the write buffer to Redis for a specific key"""
        if page_id not in self.write_buffer:
            return

        if page_id not in self.buffer_locks:
            self.buffer_locks[page_id] = asyncio.Lock()

        async with self.buffer_locks[page_id]:
            count = self.write_buffer.get(page_id, 0)
            if count > 0:
                await self.redis_manager.increment(page_id, count)
            self.write_buffer.pop(page_id, None)
        
        self.buffer_locks.pop(page_id, None)

    def _cache_validity_check(self, page_id: str) -> bool:
        """Check if cache is still valid for a page"""
        return (page_id in self.cache and 
                (datetime.now() - self.cache[page_id]["timestamp"]) < timedelta(seconds=self.CACHE_TTL))

    async def increment_visit(self, page_id: str) -> None:
        """
        Increment visit count for a page
        
        Args:
            page_id: Unique identifier for the page
        """
        if page_id not in self.buffer_locks:
            self.buffer_locks[page_id] = asyncio.Lock()

        async with self.buffer_locks[page_id]:
            self.write_buffer[page_id] = self.write_buffer.get(page_id, 0) + 1

    async def get_visit_count(self, page_id: str) -> Dict[str, Any]:
        """
        Get current visit count for a page
        
        Args:
            page_id: Unique identifier for the page
            
        Returns:
            Current visit count
        """
        visit_count = 0
        served_via = ""

        if self._cache_validity_check(page_id):
            # Using in-memory cache
            if page_id not in self.cache_locks:
                self.cache_locks[page_id] = asyncio.Lock()

            async with self.cache_locks[page_id]:
                visit_count = self.cache[page_id]["count"]
                served_via = "in-memory"

        else:
            # Flush the buffer to Redis before fetching
            await self.flush_buffer_key(page_id)

            # Fetch from Redis
            visit_count = await self.redis_manager.get(page_id)
            visit_count = visit_count if visit_count is not None else 0
            served_via = self.redis_manager.get_redis_node_from_key(page_id)
            served_via = f"redis_{served_via.split(':')[-1]}"

            # Update in-memory cache
            async with self.cache_locks.setdefault(page_id, asyncio.Lock()):
                self.cache[page_id] = {
                    "count": visit_count,
                    "timestamp": datetime.now()
                }

        # Include pending counts in buffer
        if page_id not in self.buffer_locks:
            self.buffer_locks[page_id] = asyncio.Lock()

        async with self.buffer_locks[page_id]:
            visit_count += self.write_buffer.get(page_id, 0)

        return {"visits": visit_count, "served_via": served_via}

redis_manager = RedisManager()
visit_counter_service = VisitCounterService(redis_manager)
