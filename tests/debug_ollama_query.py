import socket
import time

s = socket.socket()
s.settimeout(15)
s.connect(('127.0.0.1', 11434))

input_text = "Immediate refund dispute on invoice #9401"
selected_leaf_name = "Invoice_Tax_Exemption"

prompt_str = f"Axiom-1 System 2 Verification: An operational request arrived: \\\"{input_text}\\\". Target candidate: {selected_leaf_name}. Answer with a brief verification of whether this category fits."
body = f'{{"model":"qwen2.5-coder:1.5b","prompt":"{prompt_str}","stream":false,"options":{{"num_predict":32}}}}'
req = (
    "POST /api/generate HTTP/1.1\r\n"
    "Host: 127.0.0.1:11434\r\n"
    "Content-Type: application/json\r\n"
    f"Content-Length: {len(body)}\r\n"
    "Connection: close\r\n\r\n"
    f"{body}"
)

print("Sending request...")
s.sendall(req.encode('utf-8'))

data = b''
t0 = time.time()
while True:
    try:
        chunk = s.recv(2048)
        if not chunk:
            print("Remote closed.")
            break
        data += chunk
        print(f"Received {len(chunk)} bytes at {time.time()-t0:.2f}s")
        if b'\r\n\r\n' in data:
            headers, body_data = data.split(b'\r\n\r\n', 1)
            cl = -1
            for line in headers.decode('latin1').split('\r\n'):
                if line.lower().startswith('content-length:'):
                    cl = int(line.split(':')[1].strip())
            print(f"Content-Length: {cl}, Body received so far: {len(body_data)}")
            if cl > 0 and len(body_data) >= cl:
                print("Full body received!")
                break
    except Exception as e:
        print(f"Exception: {e}")
        break

s.close()
