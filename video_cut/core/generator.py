import os
import json
import dashscope
from dashscope import Generation

class Generator:
    def __init__(self, node_id, prompt, context):
        self.node_id = node_id
        self.prompt = prompt
        self.context = context
        
        # 尝试从多个来源读取 API Key
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            # 尝试从 api_key.txt 文件读取
            try:
                api_key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'api_key.txt')
                if os.path.exists(api_key_path):
                    with open(api_key_path, 'r') as f:
                        api_key = f.read().strip()
            except:
                pass
        
        if api_key:
            dashscope.api_key = api_key
        else:
            raise Exception("未找到 DashScope API Key，请设置环境变量 DASHSCOPE_API_KEY 或在项目根目录创建 api_key.txt 文件")

    def generate(self):
        system_prompt = self.prompt.get("system", "")
        user_prompt = "\n".join(self.prompt.get("user", []))
        
        # 替换上下文变量
        for key, value in self.context.items():
            user_prompt = user_prompt.replace(f"[{key}]", str(value))

        # 构造 messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        # 调用 DashScope API
        response = Generation.call(
            model="qwen-plus",  # 可替换为 qwen-max、qwen-turbo 等
            prompt=user_prompt,
            system=system_prompt
        )

        # 提取生成结果
        result = response.output.text
        print(f"Node {self.node_id} generated content: {result}")

        try:
            return json.loads(result[result.find("{"):result.rfind("}")+1])
        except json.JSONDecodeError:
            raise Exception(f"生成内容格式错误，非 JSON：{result}")