from video_cut.config.prompts import PROMPTS
from video_cut.config.schemas import SCHEMAS
from video_cut.core.node import Node

# DAG 定义（节点依赖）
DAG = {
    "node1": [],
    "node2": ["node1"],
    "node3": ["node2"],
    "node4": ["node3"],
    "node5": ["node3"],
    "node6": ["node3"],
    "node7": ["node3"],
    "node8": ["node3"],
    "node9": ["node3"],
    "node10": ["node1"],
    "node11": ["node1"],
    "node12": ["node3", "node4", "node5", "node6", "node7", "node8", "node9", "node10", "node11"]
}

# 节点定义
NODES = {
    node_id: Node(
        node_id=node_id,
        prompt=PROMPTS[node_id],
        schema=SCHEMAS[node_id],
        dependencies=DAG[node_id]
    )
    for node_id in DAG
}