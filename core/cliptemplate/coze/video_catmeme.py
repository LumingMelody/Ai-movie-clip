

"""
This example describes how to use the workflow interface to chat.
"""

# Our official coze sdk for Python [cozepy](https://github.com/coze-dev/coze-py)
from cozepy import COZE_CN_BASE_URL
from doubaoconfigs import coze_api_token

# Get an access_token through personal access token or oauth.
coze_api_token = coze_api_token
# The default access is api.coze.com, but if you need to access api.coze.cn,
# please use base_url to configure the api endpoint to access
coze_api_base = COZE_CN_BASE_URL

from cozepy import Coze, TokenAuth, Message, ChatStatus, MessageContentType  # noqa
import json

from core.cliptemplate.coze.transform.coze_videos_catmeme_dialogue import trans_video_catmeme




def get_video_catmeme(author,title,content=None):
    # Init the Coze client through the access_token.
    coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)

    # Create a workflow instance in Coze, copy the last number from the web link as the workflow's ID.
    workflow_id = '7496346668364677161'

    # 确保参数不为空，提供默认值
    if not title:
        title = "猫咪表情包对话"
    if not content:
        content = "生成有趣的猫咪对话内容"
    if not author:
        author = "用户"
    
    parameters={"author":author,
                "title":title,
                "content":content,
                "dialogue_type":"catmeme",  # 添加对话类型参数
                }

    # Call the coze.workflows.runs.create method to create a workflow run. The create method
    # is a non-streaming chat and will return a WorkflowRunResult class.
    workflow = coze.workflows.runs.create(
        workflow_id=workflow_id,
        parameters=parameters
    )


    print("workflow.data", workflow.data)
    response=json.loads(workflow.data)
    
    # 检查返回的数据是否有效，如果无效则生成默认对话
    if not response.get('texts') or len(response['texts']) == 0:
        print("⚠️ Coze工作流返回的texts为空，生成默认对话内容")
        # 基于输入生成默认的对话结构
        default_texts = [
            {"Asays": f"{author}说: {title}", "Bsays": "原来如此！"},
            {"Asays": "你觉得怎么样？", "Bsays": "听起来很有趣呢"},
            {"Asays": f"关于{content or '这个话题'}", "Bsays": "我学到了很多"}
        ]
        
        response.update({
            'texts': default_texts,
            'characterA': author or '角色A',
            'characterB': '小猫咪',
            'title': title or '猫咪表情包对话'
        })
        print(f"✅ 使用默认对话结构，包含{len(default_texts)}条对话")
    
    result_path=trans_video_catmeme(response)

    return result_path

if __name__ == "__main__":


# author="李小龙"
# lift_text="健康养生"
# content='''



# 电脑前的你请注意！每天3分钟椅子养生法，激活胆经助消化！现在双脚踏实地面，跟我这样做——


# 脚跟压实地面，前脚掌如蝴蝶振翅轻盈抬起，激活足弓力量。保持脚跟并拢，以脚跟为轴，脚尖缓缓外旋画弧，像在描绘八字形。


# 当膝盖外侧下方三指处（阳陵泉穴）产生酸胀感，说明成功触达胆经枢纽！这个黄金穴位掌控胆汁疏泄，持续刺激就像给肝胆做SPA。


# 单侧练习时：外展吸气3秒，回落呼气放松；双侧同步练习可趁回邮件时悄悄进行。每组保持15秒，每日5组，脂肪分解效率提升看得见！

# 记住这个秘诀：脚尖写八字，胆经自通达。办公养生两不误，让足尖的每一次转动，都成为你健康投资的零存整取！

# 急性胆囊疾病患者慎做，不适请停止
# '''


    result_path=get_video_catmeme("阳山数谷产业园","产业园区运营")