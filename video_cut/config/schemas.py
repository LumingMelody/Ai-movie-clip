import json
import os

# 获取当前文件的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
SCHEMAS_DIR = os.path.join(current_dir, "schemas")

def load_schema(filename):
    path = os.path.join(SCHEMAS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

SCHEMAS = {
    "node1": load_schema("node1.json"),
    "node2": load_schema("node2.json"),
    "node3": load_schema("node3.json"),
    "node4": load_schema("node4.json"),
    "node5": load_schema("node5.json"),
    "node6": load_schema("node6.json"),
    "node7": load_schema("node7.json"),
    "node8": load_schema("node8.json"),
    "node9": load_schema("node9.json"),
    "node10": load_schema("node10.json"),
    "node11": load_schema("node11.json"),
    "node12": load_schema("timeline.json")
}