import os
from moviepy import ImageClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip,VideoClip
import uuid

from config import get_user_data_dir

# 加载json数据（这里直接用字典代替）
data = {
    "audio_url": "https://codel-agent.oss-cn-shanghai.aliyuncs.com/zhlyy.mp3",
    "imgs": [
        "https://s.coze.cn/t/kI-AuaGw4eA/",
        "https://s.coze.cn/t/3hL-px7KRVE/",
        "https://s.coze.cn/t/JC1QqiZF2LE/",
        "https://s.coze.cn/t/iU3GzrjOtss/",
        "https://s.coze.cn/t/nUIzZleYnwI/"
    ]
}

project_id=str(uuid.uuid1())
# base_project_path="projects"
user_data_dir = get_user_data_dir()
base_project_path = os.path.join(user_data_dir, "projects")
project_path=os.path.join(base_project_path,project_id)
os.makedirs(project_path,exist_ok=True)

def download_file(url, local_filename):
    import requests
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk)
    return local_filename

# 下载背景音乐
bg_audio_path = download_file(data['audio_url'], "bg_audio.mp3")

# 下载所有图片并设置每张图片的显示时长
image_clips = []
duration_per_image = 5  # 每张图片显示5秒（可以根据需要调整）
for i, img_url in enumerate(data['imgs']):
    img_path = download_file(img_url, f"img_{i}.png")
    img_clip = ImageClip(img_path,duration=duration_per_image)
    image_clips.append(img_clip)

# 将所有图片组合成一个视频
final_video : VideoClip= concatenate_videoclips(image_clips)

# 加载背景音乐并裁剪到与视频相同长度
bg_music = AudioFileClip(bg_audio_path).subclipped(0, final_video.duration)

# 将背景音乐添加到视频中
final_video = final_video.with_audio(bg_music)

# 输出最终视频
final_video.write_videofile(os.path.join(project_path,"output1.mp4"),fps=24, codec="libx264", audio_codec="aac")