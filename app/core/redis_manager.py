import os
import redis
from typing import Dict, List, Optional, Any
from .consistent_hash import ConsistentHash
from .config import settings
from bisect import bisect_right

class RedisManager:
    MAX_POOL_CONNECTIONS = 200

    def __init__(self):
        """Initialize Redis connection pools and consistent hashing"""
        redis_urls = os.getenv("REDIS_NODES").split(",") if os.getenv("REDIS_NODES") else ["redis://redis1:6379"]
        self.connection_pools: Dict[str, redis.ConnectionPool] = {}
        self.redis_clients: Dict[str, redis.Redis] = {}
        self.consistent_hash = ConsistentHash()
        
        for redis_url in redis_urls:
            self.add_redis_instance(redis_url)
        # self.redis_client = redis.Redis.from_url(redis_nodes[0]) # Using only 1 node, more are not required for now

    def add_redis_instance(self, redis_url: str) -> None:
        if redis_url in self.redis_clients:
            return

        print(f"Adding Redis instance: {redis_url}")
        connection_pool = redis.ConnectionPool.from_url(
            redis_url, decode_responses=True, max_connections=self.MAX_POOL_CONNECTIONS
        )
        self.connection_pools[redis_url] = connection_pool
        self.redis_clients[redis_url] = redis.Redis(connection_pool=connection_pool)

        old_keys = self.consistent_hash.sorted_keys.copy()
        old_hash_ring = self.consistent_hash.hash_ring.copy()
        self.consistent_hash.add_node(redis_url)

        all_keys = list(set(self.get_all_keys()) - set(self.redis_clients[redis_url].keys()))
        
        for key in all_keys:
            node = self.consistent_hash.get_node(key)
            if node != redis_url:
                continue

            hash_value = self.consistent_hash._hash(key)
            idx = bisect_right(old_keys, hash_value) % len(old_keys)
            old_node = old_hash_ring[old_keys[idx]]

            print(f"Migrating key {key} from {old_node} to {node}")
            value = self.redis_clients[old_node].get(key)
            if value:
                self.redis_clients[node].set(key, value)
                self.redis_clients[old_node].delete(key)


    def remove_redis_instance(self, redis_url: str) -> None:
        """
        Remove a Redis instance from the manager
        """
        if redis_url not in self.redis_clients:
            return

        if len(self.redis_clients) == 1:
            print("Cannot remove the last Redis instance")
            return

        print(f"Removing Redis instance: {redis_url}")
        old_keys = self.consistent_hash.sorted_keys.copy()
        old_hash_ring = self.consistent_hash.hash_ring.copy()
        self.consistent_hash.remove_node(redis_url)
        
        all_keys = self.redis_clients[redis_url].sorted_keys()

        for key in all_keys:
            new_node = self.consistent_hash.get_node(key)
            print(f"Migrating key {key} from {redis_url} to {new_node}")
            value = self.redis_clients[redis_url].get(key)
            self.redis_clients[new_node].set(key, value)
            self.redis_clients[redis_url].delete(key)

        self.redis_clients.pop(redis_url)
        self.connection_pools.pop(redis_url)

    def get_all_keys(self) -> List[str]:
        """Get all keys from all Redis instances"""
        all_keys = []
        for redis_client in self.redis_clients.values():
            all_keys.extend(redis_client.scan_iter("*"))
        return all_keys

    def get_connection(self, key: str) -> redis.Redis:
        """
        Get Redis connection for the given key using consistent hashing
        
        Args:
            key: The key to determine which Redis node to use
            
        Returns:
            Redis client for the appropriate node
        """
        # TODO: Implement getting the appropriate Redis connection
        # 1. Use consistent hashing to determine which node should handle this key
        # 2. Return the Redis client for that node
        node = self.consistent_hash.get_node(key)
        if node is None:
            raise Exception("No Redis nodes available")
        return self.redis_clients[node]
    
    def get_redis_node_from_key(self, key: str):
        # Assuming you have a consistent hashing mechanism
        node = self.consistent_hash.get_node(key)
        if node is None:
            raise Exception("No Redis nodes available")
        return node


    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter in Redis
        
        Args:
            key: The key to increment
            amount: Amount to increment by
            
        Returns:
            New value of the counter
        """
        # TODO: Implement incrementing a counter
        # 1. Get the appropriate Redis connection
        # 2. Increment the counter
        # 3. Handle potential failures and retries
        redis_client = self.get_connection(key)
        return redis_client.incrby(key, amount)

    async def get(self, key: str) -> Optional[int]:
        """
        Get value for a key from Redis
        
        Args:
            key: The key to get
            
        Returns:
            Value of the key or None if not found
        """
        # TODO: Implement getting a value
        # 1. Get the appropriate Redis connection
        # 2. Retrieve the value
        # 3. Handle potential failures and retries
        redis_client = self.get_connection(key)
        value = redis_client.get(key)
        return int(value) if value is not None else 0
