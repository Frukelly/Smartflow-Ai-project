import socket
import threading
import json
from datetime import datetime

CLOUD_HOST = '127.0.0.1'
CLOUD_PORT = 9000

# Store node telemetry and logs
node_data = {}

# Simple SmartFlow AI decision based on telemetry
def smartflow_ai(telemetry):
    """
    If CPU > 80% or Memory > 80% or Storage > 90% -> reduce_load
    else if CPU < 30% -> increase_load
    else stable
    """
    cpu = telemetry.get("cpu_percent", 0)
    memory = telemetry.get("memory_percent", 0)
    storage = telemetry.get("storage_percent", 0)

    if cpu > 80 or memory > 80 or storage > 90:
        return "reduce_load"
    elif cpu < 30:
        return "increase_load"
    else:
        return "stable"

def handle_node(conn, addr):
    try:
        data = conn.recv(8192)
        if not data:
            return
        payload = json.loads(data.decode())
        node_id = payload.get("node_id", "unknown")
        telemetry = payload.get("telemetry", {})
        file_data = payload.get("file_data", None)

        # Update node logs
        node_data[node_id] = {
            "telemetry": telemetry,
            "last_seen": datetime.now().strftime("%H:%M:%S"),
            "last_file": file_data
        }

        # Make SmartFlow decision
        action = smartflow_ai(telemetry)
        response = {"action": action}

        # Send response back to node
        conn.send(json.dumps(response).encode())

    except Exception as e:
        print(f"Error handling node {addr}: {e}")
    finally:
        conn.close()

def cloud_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((CLOUD_HOST, CLOUD_PORT))
        s.listen()
        print(f"Cloud server listening on {CLOUD_HOST}:{CLOUD_PORT}")

        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_node, args=(conn, addr), daemon=True)
            t.start()

if __name__ == "__main__":
    cloud_server()
