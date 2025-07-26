

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

from core.cliptemplate.coze.transform.coze_videos_big_word import trans_video_big_word




def get_big_word(company_name,title,product,description ,content=None):
    # 🔥 添加调试信息
    print(f"🔍 [get_big_word] 接收到的参数:")
    print(f"   company_name: {company_name}")
    print(f"   title: {title}")
    print(f"   product: {product}")
    print(f"   description: {description}")
    print(f"   content: {content}")
    
    # Init the Coze client through the access_token.
    coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)

    # Create a workflow instance in Coze, copy the last number from the web link as the workflow's ID.
    workflow_id = '7502316696242929674'

    parameters={"author":company_name,
                "title":title,
                "product":product,
                "description":description,
                "content":content,
                }
    
    print(f"🚀 [get_big_word] 传递给Coze的参数: {parameters}")

    # Call the coze.workflows.runs.create method to create a workflow run. The create method
    # is a non-streaming chat and will return a WorkflowRunResult class.
    workflow = coze.workflows.runs.create(
        workflow_id=workflow_id,
        parameters=parameters
    )


    print("workflow.data", workflow.data)
    response=json.loads(workflow.data)
    result_path=trans_video_big_word(response)

    return result_path


if __name__ == "__main__":
    get_big_word("阳山数谷","园区运营", "测试", "测试")