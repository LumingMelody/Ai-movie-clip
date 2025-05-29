

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
import requests

from core.cliptemplate.coze.transform.coze_videos_tax_introduction import trans_video_tax_news_introduction




def get_video_introduction(author:bool,title:str,Content:str,character_img:bool=True):
    # Init the Coze client through the access_token.
    coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)

    # Create a workflow instance in Coze, copy the last number from the web link as the workflow's ID.
    workflow_id = '7496581587548864547'
    url = "https://api.coze.cn/v1/files/upload"
    headers = {
        "Authorization": "Bearer "+coze_api_token,
    }

    # 定义文件路径
    file_path = character_img

    # 打开文件并发送POST请求
    with open(file_path, 'rb') as file:
        files = {'file': file}
        response = requests.post(url, headers=headers, files=files)

    # res=requests.post('https://api.coze.cn/v1/files/upload',headers="'Authorization': 'Bearer '" + coze_api_token,form={"file":clothesurl})
    res_json=response.json()
    fileid=res_json["data"]["id"]
    parameters={"author":author,
                "character": "{\"file_id\": \""+fileid+"\"}" ,
                "Content":Content,
                "title":title,
                }

    # Call the coze.workflows.runs.create method to create a workflow run. The create method
    # is a non-streaming chat and will return a WorkflowRunResult class.
    workflow = coze.workflows.runs.create(
        workflow_id=workflow_id,
        parameters=parameters
    )


    print("workflow.data", workflow.data)
    response=json.loads(workflow.data)
    result_path=trans_video_tax_news_introduction(response)

    return result_path

if __name__ == '__main__':
    author="常熟优帮财税"
    character_img="60e4f42847c1d1da78f38.png"
    # clothesurl="https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/e52a65c1e97148f1a58ad30414d1077b.jpg~tplv-mdko3gqilj-image.image?rk3s=81d4c505&x-expires=1776161691&x-signature=RZ9IXKiJu1ySr2wW%2F%2FqaCuLC7Sc%3D&x-wf-file_name=v2-311f156bc93f8eeecbde57914439fd6d_720w.jpg"
    title="偷逃税款被处罚案件"
    Content='''2023年11月，南京市税务局在对一家纺织品制造企业的税务审查中发现，该企业存在向非农业生产者开具农产品收购发票的情况。具体表现为从城市零售商处购买羊毛并开具了收购发票。鉴于此类发票仅能提供给直接从事农业生产的个人，该企业不得不进行进项税额转出处理，金额总计达到4.75万元，并补缴了相应的增值税和滞纳金。'''

    result_path=get_video_introduction(author,title,Content,character_img)