import hashlib
from typing import List, Dict, Any
from bisect import bisect_right

class ConsistentHash:
    def __init__(self, nodes: List[str] = [], virtual_nodes: int = 100):
        """
        Initialize the consistent hash ring
        
        Args:
            nodes: List of node identifiers (parsed from comma-separated string)
            virtual_nodes: Number of virtual nodes per physical node
        """
        
        # TODO: Initialize the hash ring with virtual nodes
        # 1. For each physical node, create virtual_nodes number of virtual nodes
        # 2. Calculate hash for each virtual node and map it to the physical node
        # 3. Store the mapping in hash_ring and maintain sorted_keys
        self.virtual_nodes = virtual_nodes
        self.hash_ring : Dict[int, str] = {}
        self.sorted_keys : List[int] = []
        
        for node in nodes:
            self.add_node(node)


    def _hash(self, key: str) -> int:
        """
        Hash function to calculate hash of a key
        """
        return int(hashlib.sha1(key.encode()).hexdigest(), 16) % (2**32)

    def add_node(self, node: str) -> None:
        """
        Add a new node to the hash ring
        
        Args:
            node: Node identifier to add
        """
        # TODO: Implement adding a new node
        # 1. Create virtual nodes for the new physical node
        # 2. Update hash_ring and sorted_keys
        for i in range(self.virtual_nodes):
            virtual_key = f"{node}#{i}"
            hash_val = self._hash(virtual_key)

            if hash_val in self.hash_ring:
                continue

            self.hash_ring[hash_val] = node
            self.sorted_keys.append(hash_val)
        
        self.sorted_keys.sort()

    def remove_node(self, node: str) -> None:
        """
        Remove a node from the hash ring
        
        Args:
            node: Node identifier to remove
        """
        # TODO: Implement removing a node
        # 1. Remove all virtual nodes for the given physical node
        # 2. Update hash_ring and sorted_keys
        for i in range(self.virtual_nodes):
            virtual_key = f"{node}#{i}"
            hash_val = self._hash(virtual_key)

            if hash_val not in self.hash_ring:
                continue

            self.hash_ring.pop(hash_val)
            self.sorted_keys.remove(hash_val)

    def get_node(self, key: str) -> str:
        """
        Get the node responsible for the given key
        
        Args:
            key: The key to look up
            
        Returns:
            The node responsible for the key
        """
        # TODO: Implement node lookup
        # 1. Calculate hash of the key
        # 2. Find the first node in the ring that comes after the key's hash
        # 3. If no such node exists, wrap around to the first node
        if not self.sorted_keys:
            return ""

        key_hash = self._hash(key)
        idx = bisect_right(self.sorted_keys, key_hash)

        if idx == len(self.sorted_keys):
            return self.hash_ring[self.sorted_keys[0]]

        return self.hash_ring[self.sorted_keys[idx]]
    