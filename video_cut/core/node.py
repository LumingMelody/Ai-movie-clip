import json

from video_cut.core.generator import Generator
from video_cut.core.instance_manager import InstanceManager
from video_cut.core.validator import validate_json


class Node:
    def __init__(self, node_id, prompt, schema, dependencies):
        self.node_id = node_id
        self.prompt = prompt
        self.schema = schema
        self.dependencies = dependencies
        self.instance_manager = InstanceManager(node_id)

    def execute(self, context):
        # 尝试加载缓存
        cached = self.instance_manager.load_instance()
        if cached:
            return cached

        # 生成
        generator = Generator(self.node_id, self.prompt, context)
        output = generator.generate()

        # 校验
        validate_json(output, self.schema)

        # 保存
        self.instance_manager.save_instance(output)
        return output

    def apply_changes(self, old_output, changes):
        for key, value in changes.items():
            keys = key.split('.')
            current = old_output
            for k in keys[:-1]:
                current = current[k]
            current[keys[-1]] = value
        self.instance_manager.save_instance(old_output, version="modified")
        return old_output