
"""
This example describes how to use the workflow interface to chat.
"""

# Our official coze sdk for Python [cozepy](https://github.com/coze-dev/coze-py)
from cozepy import COZE_CN_BASE_URL
from config import load_config

# Get an access_token through personal access token or oauth.
coze_api_token = load_config()['coze']
# The default access is api.coze.com, but if you need to access api.coze.cn,
# please use base_url to configure the api endpoint to access
coze_api_base = COZE_CN_BASE_URL

from cozepy import Coze, TokenAuth, Message, ChatStatus, MessageContentType  # noqa
import json

from core.cliptemplate.coze.transform.coze_videos_advertsment_enhance import trans_videos_advertisement_enhance




def get_video_advertisement_enhance(company_name ,service ,topic , content=None ,need_change=False, add_digital_host=True,  # 添加数字人
                                    use_temp_materials=False,  # 使用正式素材目录 (materials)
                                    clip_mode=True,  # 使用随机剪辑模式
                                    upload_digital_host=False,  # ✅ 使用系统默认目录（而非上传目录）
                                    moderator_source=None,  # 不指定其他路径，使用默认系统目录
                                    enterprise_source=None,
                                    ):
    print(coze_api_token)
    # data={"audio_urls":["https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/d978d0746a904c71a2e1d56535841d0c.mp3","https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/72edb65a45964b6480520461105a312a.mp3","https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/f3fa350d20864c96b5df9174626a11a8.mp3","https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/0df148c2bd8645f088b2ab8b7f60f32e.mp3","https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/1af8d939131b428a9a1c035b20ff038c.mp3","https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/565c29db176c42cda33d2265dbf54f00.mp3","https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/9da6fa5d8ca14e7fa32e6a5d87762548.mp3","https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/82cfc97f51384025b42f8c3ed4298dd3.mp3"],"bgm":"https://lf6-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/6060583a708e40cf951517171592f9ac","company_name":"1","data":"https://p9-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/a00d53e5e60c4a958a4fbde71d3f71a6.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1779691283&x-signature=%2B1k67D%2FnWDC2PzSTIo7vFAE5v4Y%3D","output":["[1]，深 耕于[1]行业！","以别具一格的[1业务特色]，给您呈上独一无二的服务体验。","不管是面对复杂的[列举一些业务相关情况]，","还是遇到多样的需求，我们始终专业在线。","选择[1]，就等于选择安心、放心、贴心。","抖音的小伙伴们，赶紧关注我们呀，","随我们一同感受[1]行业中[1]的无穷魅力，","开启愉快合作之旅！"]}
    # result_path=trans_videos_advertisement_enhance(data,add_digital_host=False,  # 添加数字人
    #     use_temp_materials=use_temp_materials,
    #     clip_mode=clip_mode,
    #     upload_digital_host=upload_digital_host,
    #     moderator_source=moderator_source,
    #     enterprise_source=enterprise_source
    #     )
    # return result_path


    # return "projects\\f1d0ba63-3cfb-11f0-a757-c664412029c0\\final_video.mp4"
    # Init the Coze client through the access_token.
    coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)

    # Create a workflow instance in Coze, copy the last number from the web link as the workflow's ID.
    workflow_id = '7499113029830049819'

    parameters ={"company_name" :company_name,
                "service" :service,
                "topic" :topic,
                "content" :content,
                "need_change" :need_change
                }

    # Call the coze.workflows.runs.create method to create a workflow run. The create method
    # is a non-streaming chat and will return a WorkflowRunResult class.
    workflow = coze.workflows.runs.create(
        workflow_id=workflow_id,
        parameters=parameters
    )


    print("workflow.data", workflow.data)

    response =json.loads(workflow.data)
    result_path =trans_videos_advertisement_enhance(response ,add_digital_host=add_digital_host,  # 添加数字人
                                                   use_temp_materials=use_temp_materials,
                                                   clip_mode=clip_mode,
                                                   upload_digital_host=upload_digital_host,
                                                   moderator_source=moderator_source,
                                                   enterprise_source=enterprise_source
                                                   )
    return result_path


if __name__ == "__main__":
    for i in range(1):
        get_video_advertisement_enhance("阳山数谷" ,"企业园区运营" ,"园区运营" ,add_digital_host=False,  # 添加数字人
                                        use_temp_materials=False,  # 使用正式素材目录 (materials)
                                        clip_mode=True,  # 使用随机剪辑模式
                                        upload_digital_host=False,  # ✅ 使用系统默认目录（而非上传目录）
                                        moderator_source=None,  # 不指定其他路径，使用默认系统目录
                                        enterprise_source=None,  # 使用默认企业素材目录
                                        )
    # get_video_advertisement("常熟优帮财税","代理记账 税务筹划","财税")

# title="胆经自通达，办公养生两不误"

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


# result_path=get_video_stickman(author,title,content,lift_text)