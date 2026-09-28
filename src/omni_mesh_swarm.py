"""
Axiom P2P Local Mesh Swarm Protocol
Enables automatic discovery, CRDT memory-pointer synchronization, and work-stealing
across multiple Axiom workstations and devices on the local LAN.
"""

import json
import os
import socket
import sys
import threading
import time
import uuid
import psutil

SWARM_PORT = 3001
BROADCAST_IP = "255.255.255.255"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_FILE = os.path.join(PROJECT_ROOT, "skills", "learned_skills.json")

class AxiomMeshNode:
    def __init__(self, http_port: int = 3000):
        self.node_id = str(uuid.uuid4())[:8]
        self.hostname = socket.gethostname()
        self.http_port = http_port
        self.running = False
        
        # Peer Registry: {node_id: {hostname, ip, port, cpu, ram, last_seen, active_leaves}}
        self.peers = {}
        self.lock = threading.Lock()
        
        # Socket handles
        self.sock_rx = None
        self.sock_tx = None

    def start(self):
        """Starts discovery beacon transmitter and receiver threads."""
        if self.running:
            return
        self.running = True

        try:
            # Broadcast Sender Socket
            self.sock_tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock_tx.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.sock_tx.settimeout(0.2)

            # Broadcast Receiver Socket
            self.sock_rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock_rx.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock_rx.bind(("", SWARM_PORT))
            self.sock_rx.settimeout(1.0)
        except Exception as e:
            # Port might be in use or network restricted; degrade gracefully
            self.running = False
            return

        threading.Thread(target=self._tx_beacon_loop, daemon=True, name="AxiomSwarmBeaconTX").start()
        threading.Thread(target=self._rx_listener_loop, daemon=True, name="AxiomSwarmBeaconRX").start()
        threading.Thread(target=self._eviction_loop, daemon=True, name="AxiomSwarmEviction").start()

    def stop(self):
        self.running = False
        if self.sock_rx:
            try:
                self.sock_rx.close()
            except Exception:
                pass
        if self.sock_tx:
            try:
                self.sock_tx.close()
            except Exception:
                pass

    def _get_local_skill_digest(self) -> tuple:
        """Returns (count, max_timestamp) of locally learned skills."""
        if not os.path.exists(SKILLS_FILE):
            return 0, 0.0
        try:
            with open(SKILLS_FILE, 'r', encoding='utf-8') as f:
                skills = json.load(f)
            tmax = 0.0
            for s in skills:
                t = float(s.get("last_executed", s.get("created_at", 0.0)))
                if t > tmax:
                    tmax = t
            return len(skills), tmax
        except Exception:
            return 0, 0.0

    def merge_crdt_skills(self, peer_skills: list) -> int:
        """
        LWW-Element-Set CRDT Merge:
        Deterministically converges peer skill sets across nodes without conflict.
        Returns count of merged or updated skills.
        """
        if not peer_skills:
            return 0
        from src.omni_policy_optimizer import _atomic_write_json
        local_skills = []
        if os.path.exists(SKILLS_FILE):
            try:
                with open(SKILLS_FILE, 'r', encoding='utf-8') as f:
                    local_skills = json.load(f)
            except Exception:
                local_skills = []

        local_map = {s.get("skill_id"): s for s in local_skills if s.get("skill_id")}
        updated_count = 0

        for ps in peer_skills:
            sid = ps.get("skill_id")
            if not sid:
                continue
            peer_ts = float(ps.get("last_executed", ps.get("created_at", 0.0)))

            if sid not in local_map:
                local_map[sid] = ps
                updated_count += 1
            else:
                loc = local_map[sid]
                loc_ts = float(loc.get("last_executed", loc.get("created_at", 0.0)))
                if peer_ts > loc_ts:
                    loc["triggers"] = list(set(loc.get("triggers", []) + ps.get("triggers", [])))
                    loc["confidence"] = max(loc.get("confidence", 0.5), ps.get("confidence", 0.5))
                    loc["last_executed"] = peer_ts
                    updated_count += 1

        if updated_count > 0:
            try:
                _atomic_write_json(SKILLS_FILE, list(local_map.values()))
            except Exception:
                pass
        return updated_count

    def _fetch_and_merge_peer_skills(self, ip: str, port: int):
        try:
            import urllib.request
            url = f"http://{ip}:{port}/api/omni/skills"
            req = urllib.request.Request(url, headers={"User-Agent": "AxiomSwarmCRDT"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    skills = data.get("skills", [])
                    if skills:
                        self.merge_crdt_skills(skills)
        except Exception:
            pass

    def _tx_beacon_loop(self):
        while self.running:
            try:
                count, tmax = self._get_local_skill_digest()
                payload = {
                    "magic": "AXIOM_SWARM",
                    "node_id": self.node_id,
                    "hostname": self.hostname,
                    "port": self.http_port,
                    "cpu_pct": psutil.cpu_percent(),
                    "ram_pct": psutil.virtual_memory().percent,
                    "skills_count": count,
                    "skills_tmax": tmax,
                    "timestamp": time.time()
                }
                msg = json.dumps(payload).encode('utf-8')
                self.sock_tx.sendto(msg, (BROADCAST_IP, SWARM_PORT))
            except Exception:
                pass
            time.sleep(5.0)

    def _rx_listener_loop(self):
        while self.running:
            try:
                data, addr = self.sock_rx.recvfrom(2048)
                msg = json.loads(data.decode('utf-8'))
                if msg.get("magic") == "AXIOM_SWARM" and msg.get("node_id") != self.node_id:
                    peer_id = msg.get("node_id")
                    peer_port = msg.get("port", 3000)
                    with self.lock:
                        self.peers[peer_id] = {
                            "node_id": peer_id,
                            "hostname": msg.get("hostname"),
                            "ip": addr[0],
                            "port": peer_port,
                            "cpu_pct": msg.get("cpu_pct", 0),
                            "ram_pct": msg.get("ram_pct", 0),
                            "skills_count": msg.get("skills_count", 0),
                            "skills_tmax": msg.get("skills_tmax", 0.0),
                            "last_seen": time.time()
                        }
                    # CRDT synchronization trigger
                    peer_tmax = float(msg.get("skills_tmax", 0.0))
                    _, local_tmax = self._get_local_skill_digest()
                    if peer_tmax > (local_tmax + 1.0):
                        threading.Thread(
                            target=self._fetch_and_merge_peer_skills,
                            args=(addr[0], peer_port),
                            daemon=True
                        ).start()
            except socket.timeout:
                continue
            except Exception:
                time.sleep(1.0)

    def _eviction_loop(self):
        while self.running:
            time.sleep(5.0)
            now = time.time()
            with self.lock:
                stale = [pid for pid, info in self.peers.items() if (now - info.get("last_seen", 0)) > 15.0]
                for pid in stale:
                    del self.peers[pid]

    def get_swarm_status(self) -> dict:
        with self.lock:
            peers_list = list(self.peers.values())
        return {
            "node_id": self.node_id,
            "hostname": self.hostname,
            "swarm_active": self.running,
            "peers_count": len(peers_list),
            "peers": peers_list
        }

    def find_best_offload_node(self) -> Optional[dict]:
        """Finds peer node with lowest CPU load if current node is congested."""
        local_cpu = psutil.cpu_percent()
        if local_cpu < 80.0:
            return None # Process locally

        with self.lock:
            if not self.peers:
                return None
            best_peer = min(self.peers.values(), key=lambda p: p.get("cpu_pct", 100))
            if best_peer.get("cpu_pct", 100) < 60.0:
                return best_peer
        return None

# Global Singleton
mesh_node = AxiomMeshNode()
