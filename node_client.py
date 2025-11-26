import socket
import json

class NodeClient:
    def __init__(self, node_id, node_obj):
        self.node_id = node_id
        self.node = node_obj  # Your StorageVirtualNode instance
        self.active = True

    def get_telemetry(self):
        """Retrieve real telemetry from StorageVirtualNode"""
        return {
            "cpu_percent": 100 * (getattr(self.node, "cpu_used", 0) / self.node.cpu_capacity),
            "memory_percent": 100 * (getattr(self.node, "memory_used", 0) / self.node.memory_capacity),
            "storage_percent": (self.node.used_storage / self.node.total_storage) * 100,
            "active_transfers": len(self.node.active_transfers)
        }

    def send_telemetry(self, cloud_host, cloud_port):
        """Send telemetry to cloud over TCP"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((cloud_host, cloud_port))
                message = json.dumps({
                    "node_id": self.node_id,
                    "telemetry": self.get_telemetry()
                })
                s.send(message.encode())
                response = s.recv(4096)
                return json.loads(response.decode())
        except ConnectionRefusedError:
            self.active = False
            return {"action": "offline"}
