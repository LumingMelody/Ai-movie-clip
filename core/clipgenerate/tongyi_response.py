import dashscope

def get_Tongyi_response(template,content):
    messages = [
    {'role': 'system', 'content': template},
    {'role': 'user', 'content': content}
    ]
    response = dashscope.Generation.call(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key="sk-a48a1d84e015410292d07021f60b9acb",
    model="qwen-plus", # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
    messages=messages,
    result_format='message',
    enable_search=True
    )
    res=response.output.choices[0].message.content#运行
    print(res)#打印结果
    return res