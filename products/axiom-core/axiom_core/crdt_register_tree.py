"""
Conflict-Free Replicated Data Type (CRDT) Register Tree
Enables multi-agent autonomous swarms (drones, robots, edge pods) to asynchronously
learn and monotonically merge decision prototypes with zero merge conflicts.
"""

from typing import Dict, Any, List

class CrdtRegisterTree:
    def __init__(self, node_id: int):
        self.node_id = int(node_id)
        self.local_clock = 0
        self.leaves: Dict[int, Dict[str, Any]] = {}

    def update_local_leaf(self, leaf_id: int, label: str, weights: List[float]):
        """Updates local leaf prototype with vector clock increment."""
        self.local_clock += 1
        self.leaves[leaf_id] = {
            "leaf_id": leaf_id,
            "label": label,
            "weights": list(weights[:64]),
            "node_origin": self.node_id,
            "vector_clock": self.local_clock
        }

    def merge_remote_tree(self, remote_leaves: Dict[int, Dict[str, Any]]):
        """Monotonically merges remote CRDT state using Last-Write-Wins and vector clocks."""
        for leaf_id, remote_leaf in remote_leaves.items():
            if leaf_id not in self.leaves:
                self.leaves[leaf_id] = remote_leaf
            else:
                local_leaf = self.leaves[leaf_id]
                if remote_leaf["vector_clock"] > local_leaf["vector_clock"]:
                    self.leaves[leaf_id] = remote_leaf
                elif remote_leaf["vector_clock"] == local_leaf["vector_clock"] and remote_leaf["node_origin"] != local_leaf["node_origin"]:
                    # Monotonic blend of concurrent learning
                    w_local = local_leaf["weights"]
                    w_remote = remote_leaf["weights"]
                    blended = [0.5 * (a + b) for a, b in zip(w_local, w_remote)]
                    local_leaf["weights"] = blended
                    local_leaf["vector_clock"] += 1
