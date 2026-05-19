import hashlib
import bisect

class ConsistentHashRing:
    def __init__(self, nodes=None, vnodes=100):
        self.vnodes = vnodes  # Number of "virtual nodes" per physical node
        self.ring = []        # Sorted list of (hash, node_name)
        self.nodes = set()
        
        if nodes:
            for node in nodes:
                self.add_node(node)

    def _hash(self, key):
        """Returns a 32-bit integer hash of the key."""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def add_node(self, node_name):
        self.nodes.add(node_name)
        for i in range(self.vnodes):
            # Create a unique name for each virtual node
            vnode_key = f"{node_name}:{i}"
            vnode_hash = self._hash(vnode_key)
            # Add to the ring and keep it sorted
            bisect.insort(self.ring, (vnode_hash, node_name))

    def get_node(self, key):
        if not self.ring:
            return None
        key_hash = self._hash(key)
        # Find the first node with a hash >= key_hash (Clockwise)
        idx = bisect.bisect_right(self.ring, (key_hash, ""))
        # If we reach the end of the ring, wrap around to the first node
        if idx == len(self.ring):
            idx = 0
        return self.ring[idx][1]

# --- THE EXPERIMENT ---

# 1. Initialize with 5 nodes
nodes = ["Node_A", "Node_B", "Node_C", "Node_D", "Node_E"]
ch = ConsistentHashRing(nodes)
print(f"Initialized with {len(nodes)} nodes.")
# print the ring
print(f"Ring: {len(ch.ring)}")

# 2. Distribute 100,000 keys
total_keys = 100000
print(f"Distributing {total_keys} keys...")
key_assignments = {}
for i in range(total_keys):
    key = f"user_data_{i}"
    key_assignments[key] = ch.get_node(key)

print(f"Initial distribution complete with {len(nodes)} nodes.")

# 3. Add a 6th node
print("Adding Node_F...")
ch.add_node("Node_F")

# 4. Check how many keys moved
moved_count = 0
for key, old_node in key_assignments.items():
    new_node = ch.get_node(key)
    if old_node != new_node:
        moved_count += 1

percent_moved = (moved_count / total_keys) * 100
print(f"Keys moved: {moved_count} ({percent_moved:.2f}%)")
print(f"Theoretical ideal movement: {100/6:.2f}%")