import threading
import random
import time
import socket
import json
from storage_virtual_node import StorageVirtualNode

# =========================
# CLOUD SERVER INFO
# =========================
CLOUD_HOST = '127.0.0.1'
CLOUD_PORT = 9000

# =========================
# NODE CLASS (Client) WITH TELEMETRY & FAULT DETECTION
# =========================
class NodeClient:
    def __init__(self, node_id, node_obj):
        self.node_id = node_id
        self.node = node_obj
        self.active = True
        self.last_telemetry_time = time.time()  # Track last telemetry sent

    def get_telemetry(self):
        return {
            "cpu_percent": 100 * (getattr(self.node, "cpu_used", 0) / self.node.cpu_capacity),
            "memory_percent": 100 * (getattr(self.node, "memory_used", 0) / self.node.memory_capacity),
            "storage_percent": (self.node.used_storage / self.node.total_storage) * 100,
            "active_transfers": len(self.node.active_transfers)
        }

    def send_data(self, file_data=None):
        payload = {
            "node_id": self.node_id,
            "telemetry": self.get_telemetry()
        }
        if file_data:
            payload["file_data"] = file_data

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((CLOUD_HOST, CLOUD_PORT))
                s.send(json.dumps(payload).encode())
                response = s.recv(4096)
                self.last_telemetry_time = time.time()  # Update last sent time
                self.active = True
                return json.loads(response.decode())
        except ConnectionRefusedError:
            # If cloud not reachable, keep node active but mark offline
            return {"action": "offline"}

    def check_fault(self, timeout=5):
        """Mark node offline if no telemetry sent in `timeout` seconds"""
        if time.time() - self.last_telemetry_time > timeout:
            self.active = False

# =========================
# SMARTFLOW DECISION LOGIC
# =========================
def smartflow_decision(response):
    action = response.get("action", "stable")
    if action == "reduce_load":
        return 1
    elif action == "stable":
        return 2
    else:
        return 3

# =========================
# NODE THREAD FUNCTION
# =========================
def node_thread(node: NodeClient):
    while True:
        file_size = random.randint(50, 200) * 1024 * 1024
        file_name = f"data_{int(time.time())}.zip"
        file_data = {"name": file_name, "size": file_size}

        response = node.send_data(file_data)
        chunks = smartflow_decision(response)

        print(f"{node.node_id} sent {file_name} ({file_size//1024//1024}MB), "
              f"cloud response: {response}, chunks this round: {chunks}")

        time.sleep(random.randint(1, 3))

# =========================
# DASHBOARD THREAD
# =========================
def dashboard_thread(nodes):
    while True:
        print("\033[H\033[J", end="")
        print("="*50)
        print("NETWORK DASHBOARD")
        print("="*50)
        for node in nodes:
            node.check_fault(timeout=5)  # Check if node is offline
            telemetry = node.get_telemetry()
            status = "ACTIVE" if node.active else "OFFLINE"
            print(f"{node.node_id} | Status: {status} | "
                  f"CPU: {telemetry['cpu_percent']:.2f}% | "
                  f"Memory: {telemetry['memory_percent']:.2f}% | "
                  f"Storage: {telemetry['storage_percent']:.2f}% | "
                  f"Active Transfers: {telemetry['active_transfers']}")
        print("="*50)
        time.sleep(2)

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    node1_obj = StorageVirtualNode("node1", 4, 16, 500, 1000)
    node2_obj = StorageVirtualNode("node2", 8, 32, 1000, 2000)

    nodes = [NodeClient("node1", node1_obj), NodeClient("node2", node2_obj)]

    for node in nodes:
        t = threading.Thread(target=node_thread, args=(node,), daemon=True)
        t.start()

    dash_thread = threading.Thread(target=dashboard_thread, args=(nodes,), daemon=True)
    dash_thread.start()

    while True:
        time.sleep(1)
