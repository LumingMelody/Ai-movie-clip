import os
import json
from datetime import datetime

DATA_DIR = "data"

class InstanceManager:
    def __init__(self, node_id):
        self.node_id = node_id
        self.node_dir = os.path.join(DATA_DIR, node_id)
        os.makedirs(self.node_dir, exist_ok=True)

    def save_instance(self, data, version="latest"):
        filename = f"{self.node_id}_{version}.json"
        path = os.path.join(self.node_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_instance(self, version="latest"):
        filename = f"{self.node_id}_{version}.json"
        path = os.path.join(self.node_dir, filename)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)