import socket
import time

s = socket.socket()
s.settimeout(15)
s.connect(('127.0.0.1', 11434))
body = '{"model":"qwen2.5-coder:1.5b","prompt":"hi","stream":false}'
req = (
    "POST /api/generate HTTP/1.1\r\n"
    "Host: 127.0.0.1:11434\r\n"
    "Content-Type: application/json\r\n"
    f"Content-Length: {len(body)}\r\n"
    "Connection: close\r\n\r\n"
    f"{body}"
)
s.sendall(req.encode('utf-8'))

data = b''
t0 = time.time()
while True:
    try:
        chunk = s.recv(4096)
        if not chunk:
            print("Socket closed by remote.")
            break
        data += chunk
        # If full json received (ends with }\n)
        if b'"done":true' in data:
            print(f"Done detected after {time.time()-t0:.2f}s!")
            break
    except socket.timeout:
        print("Socket timed out!")
        break

s.close()
header_part = data.split(b'\r\n\r\n')[0].decode('latin1')
print("=== HEADERS ===")
print(header_part)
print("=== TOTAL DATA LENGTH ===", len(data))
