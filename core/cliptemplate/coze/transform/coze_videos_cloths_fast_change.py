import os
from moviepy import ImageClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip,concatenate_audioclips,VideoFileClip
from moviepy.video.fx.Resize import Resize
import uuid



def trans_videos_clothes_fast_change(data:dict):
    project_id=str(uuid.uuid1())
    base_project_path="projects"
    project_path=os.path.join(base_project_path,project_id)
    os.makedirs(project_path,exist_ok=True)
    def download_file(url, local_filename):
        import requests
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            local_filename=os.path.join(project_path, local_filename)
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
        return local_filename

    # 下载所有资源
    # background_image_path = download_file(data['base_img'], "background.png")
    # audio_clip = AudioFileClip(download_file(data['bgm_audio'], "bgm_audio.mp3"))


    image_clips = []



    video_file_clips=VideoFileClip("openscene.mp4")
    image_clips.append(video_file_clips)
    # 下载图片并生成视频片段
    for i, img_url in enumerate(data['img_lists']):
        img_path = download_file(img_url, f"img_{i}.png")
        img_clip = ImageClip(img_path,duration=1.2)  # 每张图片显示2秒

        # 定义一个函数来应用放大效果
        # def zoom_in_effect(get_frame, t):
        #     if t < 1.5:  # 在前1.5秒保持原始大小
        #         return get_frame(t)
        #     else:  # 在最后0.5秒快速放大到1.2倍
        #         original_size = img_clip.size
        #         scale_factor = 1 + (t - 1.5) * (0.2 / 0.5)  # 快速放大到1.2倍
        #         new_size = (original_size[0] * scale_factor, original_size[1] * scale_factor)
        #         frame = get_frame(t)
        #         resized_frame = Resize.resizer(frame,new_size)
        #         return resized_frame

        # 应用放大效果
        img_clip:ImageClip = img_clip.with_effects_on_subclip([Resize(lambda t: 1 + 10 *(t - 1.05) if t >= 1 else 1)],start_time=0) 


        image_clips.append(img_clip)


    # 创建背景图片clip
    # background_clip = ImageClip(background_image_path,duration=sum([clip.duration for clip in image_clips]))

    # 将所有图片片段拼接起来
    final_image_clips = concatenate_videoclips(image_clips,method="compose")
    audio_clip = AudioFileClip("bgms.mp3")
    final_audio=concatenate_audioclips([video_file_clips.audio,audio_clip])
    # 将图片叠加到背景图片上
    # final_video = CompositeVideoClip([background_clip.with_position("center")]+[final_image_clips.with_position("center")])
    final_video=final_image_clips
    # 如果音频总时长超过视频时长，则裁剪音频
    if final_audio.duration > final_video.duration:
        final_audio = final_audio.subclipped(0, final_video.duration)
    else:
        # 若视频时长超过音频时长，则重复最后一个音频片段直到覆盖整个视频长度
        while final_audio.duration < final_video.duration:
            final_audio = concatenate_audioclips([final_audio, final_audio.subclipped(0, final_video.duration - final_audio.duration)])

    # 添加音频到视频
    final_video = final_video.with_audio(final_audio)

    out_path=os.path.join(project_path,"final_video.mp4")
    # 输出最终视频
    final_video.write_videofile(out_path, codec="libx264", fps=24)
if __name__ == "__main__":
    # 加载json数据（这里直接用字典代替）
    data = {
    "base_img": "https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/3c9f868be91e45c39f8ed1551ed1bb98.png~tplv-mdko3gqilj-image.image?rk3s=81d4c505&x-expires=1776183577&x-signature=fVLYyAgWqH5gjoD2Cpp7dDCZgp0%3D&x-wf-file_name=43b671486f74468ba364ec9106560fe5%7Etplv-5jbd59dj06-image.png",
    "bgm_audio": "https://coze-tmp-file.oss-cn-shenzhen.aliyuncs.com/2025_03_20/732558dd-30dd-402f-880d-3a49f44fc71e.mp3",
    "img_lists": [
        "http://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/1d/d7/20250420/64972d08/26091f7b-f39b-4f8f-9cb2-85a7d0f4aab6_tryon.jpg?Expires=1745172811&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=voyjID50SVLp9bJf4aDryG%2B2Wig%3D",
        "http://dashscope-result-hz.oss-cn-hangzhou.aliyuncs.com/1d/5b/20250420/6f6a8f93/45ebafe4-13f1-4935-8f5b-c495e4742b7d_tryon.jpg?Expires=1745172812&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=%2FsbDQIacF6ra2rQkgBq3Vwc5UxA%3D",
        "http://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/1d/a0/20250420/64972d08/e3617b13-595a-47d4-a110-42ad73e5f147_tryon.jpg?Expires=1745172825&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=kwvVEcmIhviEpnr73ncqfkSK6x8%3D",
        "http://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/1d/e1/20250420/64972d08/6902537c-504a-4a05-b585-2199871c41ea_tryon.jpg?Expires=1745172824&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=ZSL4nFR%2BB34QCyqTQ%2F3cKCA5XhQ%3D",
        "http://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/1d/e0/20250420/64972d08/054e6149-ea50-45e1-aef1-4a99b34a7304_tryon.jpg?Expires=1745172839&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=VlVctKf2esFqrrbxDRa408EV964%3D",
        "http://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/1d/cb/20250420/64972d08/5e213a7c-23cd-4c5f-87e4-ae381b42e6a8_tryon.jpg?Expires=1745172839&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=ea7WOSpNCsDTRDGtyHoea3x9iM4%3D",
        "http://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/1d/12/20250420/64972d08/9ec6bea4-db17-45cb-8598-cbe63e1b3cea_tryon.jpg?Expires=1745172851&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=TRAfdNPIu4OAFMyhn2HXqN3Fyv8%3D",
        "http://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/1d/68/20250420/64972d08/afa3514f-1080-42bb-95d2-7fd66835e190_tryon.jpg?Expires=1745172851&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=XUMtqqapzXXazUF1rFmkzgNFqdE%3D",
        "http://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/1d/a3/20250420/e736178b/286c3dd7-e8e7-44dc-88d3-7bf3a0b51512_tryon.jpg?Expires=1745172863&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=lcnuNG4Zh%2BrYrh6YUr%2BdQnoDmZM%3D",
        "http://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/1d/a0/20250420/e736178b/75f2cee9-9ec4-46ea-b5fd-6da226ca9c52_tryon.jpg?Expires=1745172863&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=EmZFPvsxEHYrkdDtqEzbqFMyzVM%3D",
        "http://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/1d/05/20250420/64972d08/ab0cd9ed-8d41-4216-8b4f-c6973dcfce6c_tryon.jpg?Expires=1745172876&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=5FKs1A7%2FLx0MCGcpzTSSstNXjRc%3D",
        "http://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/1d/8d/20250420/64972d08/c0e27ae0-9713-4d62-9606-a448dcab28df_tryon.jpg?Expires=1745172875&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=Tte%2Bcu8wgBvIavlHEocpGO9RzuE%3D"
    ]
    }
    trans_videos_clothes_fast_change(data)