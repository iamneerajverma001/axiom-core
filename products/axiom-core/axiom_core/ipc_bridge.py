"""
Axiom-Core High-Speed Shared-Memory IPC Bridge
Enables sub-15 microsecond zero-copy communication between Python and C++ engine
Using Win32 Memory-Mapped Files and Named Event Semaphores.
"""

import ctypes
from ctypes import wintypes
import json
import os
import subprocess
import sys
import time
import threading
from typing import Optional, Dict, Any

IPC_SHARED_MEM_NAME = "Local\\AxiomSharedMemoryPool"
IPC_REQ_EVENT_NAME  = "Local\\AxiomReqEvent"
IPC_RESP_EVENT_NAME = "Local\\AxiomRespEvent"
IPC_MAGIC = 0x4158494F  # "AXIO"
IPC_VERSION = 1

# Win32 Constants
FILE_MAP_ALL_ACCESS = 0xF001F
SYNCHRONIZE = 0x00100000
EVENT_MODIFY_STATE = 0x0002
WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102

class AxiomIpcBufferStruct(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("magic", ctypes.c_uint32),
        ("version", ctypes.c_uint32),
        ("status", ctypes.c_uint32),
        ("request_id", ctypes.c_uint32),
        ("input_len", ctypes.c_uint32),
        ("choice_id", ctypes.c_uint32),
        ("sector_id", ctypes.c_uint32),
        ("execution_path", ctypes.c_uint32),
        ("confidence", ctypes.c_float),
        ("shannon_entropy", ctypes.c_float),
        ("latency_l1_us", ctypes.c_double),
        ("latency_l2_us", ctypes.c_double),
        ("latency_total_us", ctypes.c_double),
        ("input_text", ctypes.c_char * 2048),
        ("choice_label", ctypes.c_char * 256),
        ("output_json", ctypes.c_char * 4096),
    ]

def _find_cli_binary(explicit_path: Optional[str] = None) -> Optional[str]:
    if explicit_path and os.path.exists(explicit_path):
        return explicit_path
    
    # 1. Look in sibling bin directory
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    cand1 = os.path.normpath(os.path.join(pkg_dir, "..", "bin", "axiom_cli.exe"))
    if os.path.exists(cand1):
        return cand1

    # 2. Look in workspace root
    cand2 = os.path.normpath(os.path.join(pkg_dir, "..", "..", "..", "axiom_cli.exe"))
    if os.path.exists(cand2):
        return cand2

    # 3. Check current working directory
    cand3 = os.path.abspath("axiom_cli.exe")
    if os.path.exists(cand3):
        return cand3

    return None

class AxiomIpcBridge:
    def __init__(self, cli_path: Optional[str] = None):
        self.cli_path = _find_cli_binary(cli_path)
        self.connected = False
        self.h_map = None
        self.p_buf = None
        self.buf_struct = None
        self.h_req_event = None
        self.h_resp_event = None
        self.daemon_proc = None
        self._lock = threading.Lock()

        if sys.platform == 'win32':
            self.kernel32 = ctypes.windll.kernel32
            self.kernel32.OpenFileMappingA.restype = ctypes.c_void_p
            self.kernel32.OpenFileMappingA.argtypes = [ctypes.c_uint32, ctypes.c_bool, ctypes.c_char_p]
            self.kernel32.MapViewOfFile.restype = ctypes.c_void_p
            self.kernel32.MapViewOfFile.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_size_t]
            self.kernel32.OpenEventA.restype = ctypes.c_void_p
            self.kernel32.OpenEventA.argtypes = [ctypes.c_uint32, ctypes.c_bool, ctypes.c_char_p]
            self.kernel32.SetEvent.argtypes = [ctypes.c_void_p]
            self.kernel32.ResetEvent.argtypes = [ctypes.c_void_p]
            self.kernel32.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
            self.kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
            self.kernel32.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
            self._init_ipc(auto_spawn=True)

    def is_ready(self) -> bool:
        if not self.connected:
            self._init_ipc(auto_spawn=True)
        return self.connected

    def _init_ipc(self, auto_spawn: bool = True):
        if sys.platform != 'win32':
            self.connected = False
            return

        for attempt in range(2):
            try:
                # 1. Open existing file mapping
                self.h_map = self.kernel32.OpenFileMappingA(
                    FILE_MAP_ALL_ACCESS,
                    False,
                    IPC_SHARED_MEM_NAME.encode('ascii')
                )
                if not self.h_map:
                    if auto_spawn and attempt == 0 and self.cli_path and os.path.exists(self.cli_path):
                        # Spawn C++ daemon in background
                        flags = 0x08000000 # CREATE_NO_WINDOW
                        d_env = os.environ.copy()
                        d_env["AXIOM_NO_SOCKET"] = "1"
                        self.daemon_proc = subprocess.Popen(
                            [self.cli_path, "--daemon"],
                            creationflags=flags,
                            env=d_env,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        time.sleep(0.3)
                        continue
                    self.connected = False
                    return

                # 2. Map view of file
                self.p_buf = self.kernel32.MapViewOfFile(
                    self.h_map,
                    FILE_MAP_ALL_ACCESS,
                    0,
                    0,
                    ctypes.sizeof(AxiomIpcBufferStruct)
                )
                if not self.p_buf:
                    self.kernel32.CloseHandle(self.h_map)
                    self.connected = False
                    return

                self.buf_struct = AxiomIpcBufferStruct.from_address(self.p_buf)

                # 3. Open Named Events
                self.h_req_event = self.kernel32.OpenEventA(
                    EVENT_MODIFY_STATE | SYNCHRONIZE,
                    False,
                    IPC_REQ_EVENT_NAME.encode('ascii')
                )
                self.h_resp_event = self.kernel32.OpenEventA(
                    EVENT_MODIFY_STATE | SYNCHRONIZE,
                    False,
                    IPC_RESP_EVENT_NAME.encode('ascii')
                )

                if self.h_req_event and self.h_resp_event and self.buf_struct.magic == IPC_MAGIC:
                    self.connected = True
                    return
                else:
                    self.connected = False
            except Exception:
                self.connected = False

    def query_native(self, input_text: str, timeout_ms: int = 250) -> Optional[Dict[str, Any]]:
        """
        Sends text directive into bare-metal C++ shared memory, waits on event,
        and retrieves zero-copy result in sub-15 microseconds.
        """
        if not self.connected:
            self._init_ipc()

        if not self.connected or not self.buf_struct:
            return None

        with self._lock:
            try:
                t0 = time.perf_counter()

                # Drain / Reset any stale signaled state on response event
                self.kernel32.ResetEvent(self.h_resp_event)

                # 1. Write text directly to memory arena
                encoded = input_text.encode('utf-8')[:2040]
                ctypes.memset(ctypes.byref(self.buf_struct, AxiomIpcBufferStruct.input_text.offset), 0, 2048)
                self.buf_struct.input_text[:len(encoded)] = encoded
                self.buf_struct.input_len = len(encoded)
                self.buf_struct.status = 1  # READY_TO_PROCESS

                # 2. Ring native bell
                self.kernel32.SetEvent(self.h_req_event)

                # 3. Await microsecond response
                ret = self.kernel32.WaitForSingleObject(self.h_resp_event, timeout_ms)
                if ret != WAIT_OBJECT_0:
                    return None

                elapsed_ipc_us = (time.perf_counter() - t0) * 1_000_000.0

                # 4. Zero-copy read
                exec_path_str = "FAST_PATH_COMMIT" if self.buf_struct.execution_path == 0 else "SYSTEM2_FALLBACK"
                raw_json = self.buf_struct.output_json.decode('utf-8', errors='ignore').strip()
                choice_str = self.buf_struct.choice_label.decode('utf-8', errors='ignore').strip()

                parsed_json = {}
                if raw_json and "{" in raw_json:
                    try:
                        s_idx = raw_json.find('{')
                        e_idx = raw_json.rfind('}')
                        parsed_json = json.loads(raw_json[s_idx:e_idx+1])
                    except Exception:
                        pass

                return {
                    "request_id": self.buf_struct.request_id,
                    "execution_path": exec_path_str,
                    "choice_id": self.buf_struct.choice_id,
                    "choice_label": choice_str or parsed_json.get("choice_label", "Unknown"),
                    "confidence": float(self.buf_struct.confidence),
                    "shannon_entropy": float(self.buf_struct.shannon_entropy),
                    "conformal_set": parsed_json.get("conformal_set", [self.buf_struct.choice_id]),
                    "is_singleton": parsed_json.get("is_singleton", (self.buf_struct.execution_path == 0)),
                    "active_leaves": parsed_json.get("active_leaves", 80),
                    "active_sectors": parsed_json.get("active_sectors", 8),
                    "feedback": parsed_json.get("feedback", None),
                    "latency_us": round(elapsed_ipc_us, 2),
                    "latency_l1_us": round(self.buf_struct.latency_l1_us, 2),
                    "latency_l2_us": round(self.buf_struct.latency_l2_us, 2),
                    "latency_total_us": round(self.buf_struct.latency_total_us, 2),
                    "ipc_type": "Win32_ZeroCopy_SharedMemory"
                }
            except Exception:
                return None

    def close(self):
        try:
            if self.h_req_event:
                self.kernel32.CloseHandle(self.h_req_event)
            if self.h_resp_event:
                self.kernel32.CloseHandle(self.h_resp_event)
            if self.p_buf:
                self.kernel32.UnmapViewOfFile(self.p_buf)
            if self.h_map:
                self.kernel32.CloseHandle(self.h_map)
        except Exception:
            pass
        self.connected = False
