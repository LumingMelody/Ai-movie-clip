

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

from core.cliptemplate.coze.transform.coze_videos_cloths_fast_change import trans_videos_clothes_fast_change




def get_videos_clothes_fast_change(has_figure:bool,clothesurl:str,description:str,is_down:bool=True):
    # Init the Coze client through the access_token.
    coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)

    # Create a workflow instance in Coze, copy the last number from the web link as the workflow's ID.
    workflow_id = '7495051166088020020'
    url = "https://api.coze.cn/v1/files/upload"
    headers = {
        "Authorization": "Bearer "+coze_api_token,
    }

    # 定义文件路径
    file_path = clothesurl

    # 打开文件并发送POST请求
    with open(file_path, 'rb') as file:
        files = {'file': file}
        response = requests.post(url, headers=headers, files=files)

    # res=requests.post('https://api.coze.cn/v1/files/upload',headers="'Authorization': 'Bearer '" + coze_api_token,form={"file":clothesurl})
    res_json=response.json()
    fileid=res_json["data"]["id"]
    parameters={"has_figure":has_figure,
                "clothes": "{\"file_id\": \""+fileid+"\"}" ,
                "description":description,
                "is_down":is_down,
                }

    # Call the coze.workflows.runs.create method to create a workflow run. The create method
    # is a non-streaming chat and will return a WorkflowRunResult class.
    workflow = coze.workflows.runs.create(
        workflow_id=workflow_id,
        parameters=parameters
    )


    print("workflow.data", workflow.data)
    response=json.loads(workflow.data)
    result_path=trans_videos_clothes_fast_change(response)

    return result_path

if __name__ == '__main__':
    has_figure=False
    clothesurl="C:\\Users\\17909\\Downloads\\43b671486f74468ba364ec9106560fe5~tplv-5jbd59dj06-image.png"
    # clothesurl="https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/e52a65c1e97148f1a58ad30414d1077b.jpg~tplv-mdko3gqilj-image.image?rk3s=81d4c505&x-expires=1776161691&x-signature=RZ9IXKiJu1ySr2wW%2F%2FqaCuLC7Sc%3D&x-wf-file_name=v2-311f156bc93f8eeecbde57914439fd6d_720w.jpg"
    description="适合40-60岁中年妇女的纺织毛衣"
    is_down=False


    result_path=get_videos_clothes_fast_change(has_figure,clothesurl,description,is_down)