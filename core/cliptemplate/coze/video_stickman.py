

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

from core.cliptemplate.coze.transform.coze_videos_trans_stickman import coze_stickman_video_transfrom




def get_video_stickman(author,title,content=None,lift_text="科普动画"):
    # Init the Coze client through the access_token.
    coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)

    # Create a workflow instance in Coze, copy the last number from the web link as the workflow's ID.
    workflow_id = '7492049941977301046'

    parameters={"author":author,
                "title":title,
                "content":content,
                "lift_text":lift_text,
                }

    # Call the coze.workflows.runs.create method to create a workflow run. The create method
    # is a non-streaming chat and will return a WorkflowRunResult class.
    workflow = coze.workflows.runs.create(
        workflow_id=workflow_id,
        parameters=parameters
    )


    print("workflow.data", workflow.data)
    response=json.loads(workflow.data)
    result_path=coze_stickman_video_transfrom(response)

    return result_path


if __name__ == "__main__":
    get_video_stickman("常熟优帮财税","财税合规",lift_text="财税科普")

# content='''



# 电脑前的你请注意！每天3分钟椅子养生法，激活胆经助消化！现在双脚踏实地面，跟我这样做——


# 脚跟压实地面，前脚掌如蝴蝶振翅轻盈抬起，激活足弓力量。保持脚跟并拢，以脚跟为轴，脚尖缓缓外旋画弧，像在描绘八字形。


# 当膝盖外侧下方三指处（阳陵泉穴）产生酸胀感，说明成功触达胆经枢纽！这个黄金穴位掌控胆汁疏泄，持续刺激就像给肝胆做SPA。


# 单侧练习时：外展吸气3秒，回落呼气放松；双侧同步练习可趁回邮件时悄悄进行。每组保持15秒，每日5组，脂肪分解效率提升看得见！

# 记住这个秘诀：脚尖写八字，胆经自通达。办公养生两不误，让足尖的每一次转动，都成为你健康投资的零存整取！

# 急性胆囊疾病患者慎做，不适请停止
# '''
# title="胆经自通达，办公养生两不误"

# author="李小龙"
# lift_text="健康养生"

# result_path=get_video_stickman(author,title,content,lift_text)