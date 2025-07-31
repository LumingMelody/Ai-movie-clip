from video_cut.core.dag_engine import DAGEngine
from video_cut.core.instance_manager import InstanceManager
from video_cut.core.nl_processor import NLProcessor


class UnifiedController:
    def __init__(self, dag, nodes):
        self.dag_engine = DAGEngine(dag)
        self.nodes = nodes
        self.outputs = {}
        self.nl_processor = NLProcessor()

    def load_cache(self):
        for node_id in self.nodes:
            manager = InstanceManager(node_id)
            cached = manager.load_instance()
            if cached:
                self.outputs[node_id] = cached

    def run_generate(self, context):
        execution_order = self.dag_engine.topological_sort()
        for node_id in execution_order:
            node = self.nodes[node_id]
            output = node.execute(context)
            self.outputs[node_id] = output
            context[node_id] = output
        return self.outputs

    def run_modify(self, modify_data):
        modified_node_id = modify_data["node_id"]
        changes = modify_data["changes"]

        old_output = self.outputs.get(modified_node_id)
        if not old_output:
            raise ValueError(f"节点 {modified_node_id} 尚未生成，无法修改")

        modified_node = self.nodes[modified_node_id]
        new_output = modified_node.apply_changes(old_output, changes)
        self.outputs[modified_node_id] = new_output

        affected_nodes = self.dag_engine.get_affected_nodes(modified_node_id)
        for node_id in affected_nodes:
            node = self.nodes[node_id]
            new_output = node.execute(self.outputs)
            self.outputs[node_id] = new_output

        return self.outputs

    def run_nl_generate(self, natural_language_input):
        """处理自然语言输入并生成视频"""
        # 将自然语言转换为大纲
        outline = self.nl_processor.process_natural_language(natural_language_input)
        
        # 创建context
        context = {
            "大纲内容": outline
        }
        
        # 运行生成流程
        return self.run_generate(context)

    def handle_input(self, user_input):
        self.load_cache()
        if user_input["type"] == "generate":
            return self.run_generate(user_input.get("context", {}))
        elif user_input["type"] == "modify":
            return self.run_modify(user_input.get("modify", {}))
        elif user_input["type"] == "nl_generate":
            # 处理自然语言生成
            return self.run_nl_generate(user_input.get("natural_language", ""))
        else:
            raise ValueError("不支持的请求类型")