"""
Tests for CyberSecurity Packet Guard
"""

import sys
import os
import unittest
import time

pkg_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

from solutions.cybersecurity_packet_guard.packet_guard import (
    PacketGuard, PacketHeader, TCP_SYN, TCP_FIN, TCP_ACK
)

class TestPacketGuard(unittest.TestCase):
    def setUp(self):
        self.guard = PacketGuard()

    def test_clean_https_packet(self):
        pkt = PacketHeader(
            packet_id=1,
            src_ip="192.168.1.50",
            dst_ip="104.18.25.1",
            src_port=54321,
            dst_port=443,
            protocol=6,
            tcp_flags=TCP_ACK,
            payload_len=512,
            window_size=65535
        )
        res = self.guard.inspect_packet(pkt)
        self.assertEqual(res["action"], "PASS")
        self.assertLess(res["latency_us"], 1000.0) # Sub-millisecond pure-Python SLA


    def test_blocked_smb_port_drop(self):
        pkt = PacketHeader(
            packet_id=2,
            src_ip="10.0.0.99",
            dst_ip="192.168.1.10",
            src_port=40000,
            dst_port=445, # SMB
            protocol=6,
            tcp_flags=TCP_SYN,
            payload_len=0,
            window_size=1024
        )
        res = self.guard.inspect_packet(pkt)
        self.assertEqual(res["action"], "DROP")
        self.assertIn("BLOCKED_PORT_445", res["reason"])

    def test_syn_fin_stealth_scan_drop(self):
        pkt = PacketHeader(
            packet_id=3,
            src_ip="10.0.0.88",
            dst_ip="192.168.1.10",
            src_port=40001,
            dst_port=80,
            protocol=6,
            tcp_flags=TCP_SYN | TCP_FIN, # Illegal combination
            payload_len=0,
            window_size=1024
        )
        res = self.guard.inspect_packet(pkt)
        self.assertEqual(res["action"], "DROP")
        self.assertIn("MALFORMED_TCP_SYN_FIN", res["reason"])

    def test_wire_speed_throughput(self):
        t0 = time.perf_counter()
        count = 10_000
        for i in range(count):
            pkt = PacketHeader(
                packet_id=i,
                src_ip="192.168.1.100",
                dst_ip="8.8.8.8",
                src_port=10000 + (i % 50000),
                dst_port=53,
                protocol=17,
                tcp_flags=0,
                payload_len=64,
                window_size=0
            )
            self.guard.inspect_packet(pkt)
        elapsed = time.perf_counter() - t0
        rate = count / elapsed
        print(f"\nPacket Guard: {count:,} packets inspected in {elapsed*1000:.2f}ms ({rate:,.0f} pkts/sec)")
        self.assertGreater(rate, 25_000)

if __name__ == "__main__":

    unittest.main()
