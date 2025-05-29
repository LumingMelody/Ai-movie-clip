

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

from core.cliptemplate.coze.transform.coze_video_dgh_img_insert import trans_dgh_img_insert




def get_video_dgh_img_insert(title,video_file_path,content=None,need_change=False):
    # Init the Coze client through the access_token.
    coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)

    # Create a workflow instance in Coze, copy the last number from the web link as the workflow's ID.
    workflow_id = '7501332485470797865'

    parameters={"title":title,
                "content":content,
                "need_change":need_change,
                }

    # Call the coze.workflows.runs.create method to create a workflow run. The create method
    # is a non-streaming chat and will return a WorkflowRunResult class.
    workflow = coze.workflows.runs.create(
        workflow_id=workflow_id,
        parameters=parameters
    )


    print("workflow.data", workflow.data)
    response=json.loads(workflow.data)
    result_path=trans_dgh_img_insert(response,video_file_path)

    return result_path


if __name__ == "__main__":
    filepath="1\\2日.mp4"
    get_video_dgh_img_insert("财税",filepath,''' ''',False)
                                
#     for i in range(10):
#         get_video_advertisement("常熟优帮财税","全过程代理记账 财务合规 企业内控 重大税务筹划","财税",'''
#                                 在当前这个智慧税务迅速发展、财税管理日趋复杂的背景下，企业面临前所未有的挑战。随着税务利用大数据和智能AI技术对企业数据的全面掌握，任何不规范之处都难逃法眼，这无疑增加了企业的涉税风险。与此同时，财政压力的上升也促使税务监管日益严格，使得强化财税合规成为企业发展的必由之路。

# 常熟优帮财税凭借超过20年的税务及会计事务所实践经验，以及一体化管理模式的优势脱颖而出。我们拥有一支资深税务师和注册会计师组成的专业团队，能够为企业提供全方位的财税合规服务——从代理记账到构建完善的企业内部控制体系，从税务架构设计到常年税务顾问支持，从重大交易事项的税收筹划到纳税评估风险应对与稽查自查辅导，再到财务和税务内部审计等。我们的服务旨在为企业搭建一个功能齐全的财务与税务部门，通过专业的解决方案帮助企业有效规避财税风险，合法降低税负。

# 我们秉持诚信为本、客户至上的原则，严格遵守职业道德，确保客户信息的安全与保密，致力于在保障企业合规经营的前提下，助力其实现可持续发展目标。
                                
#                                 ''',True)
#     # get_video_advertisement("常熟优帮财税","代理记账 税务筹划","财税")

# # title="胆经自通达，办公养生两不误"

# # author="李小龙"
# # lift_text="健康养生"
# # content='''



# 电脑前的你请注意！每天3分钟椅子养生法，激活胆经助消化！现在双脚踏实地面，跟我这样做——


# 脚跟压实地面，前脚掌如蝴蝶振翅轻盈抬起，激活足弓力量。保持脚跟并拢，以脚跟为轴，脚尖缓缓外旋画弧，像在描绘八字形。


# 当膝盖外侧下方三指处（阳陵泉穴）产生酸胀感，说明成功触达胆经枢纽！这个黄金穴位掌控胆汁疏泄，持续刺激就像给肝胆做SPA。


# 单侧练习时：外展吸气3秒，回落呼气放松；双侧同步练习可趁回邮件时悄悄进行。每组保持15秒，每日5组，脂肪分解效率提升看得见！

# 记住这个秘诀：脚尖写八字，胆经自通达。办公养生两不误，让足尖的每一次转动，都成为你健康投资的零存整取！

# 急性胆囊疾病患者慎做，不适请停止
# '''


# result_path=get_video_stickman(author,title,content,lift_text)