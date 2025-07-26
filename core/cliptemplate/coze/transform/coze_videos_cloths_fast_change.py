import os
from moviepy import ImageClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip, concatenate_audioclips, \
    VideoFileClip
from moviepy.video.fx.Resize import Resize
import uuid

from config import get_user_data_dir


def trans_videos_clothes_fast_change(data: dict) -> str:
    project_id = str(uuid.uuid1())
    user_data_dir = get_user_data_dir()
    base_project_path = os.path.join(user_data_dir, "projects")
    project_path = os.path.join(base_project_path, project_id)
    os.makedirs(project_path, exist_ok=True)

    def download_file(url, local_filename):
        import requests
        # 检查URL是否为空
        if not url or url.strip() == "":
            print(f"⚠️ 跳过空URL: {url}")
            return None

        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                local_filename = os.path.join(project_path, local_filename)
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return local_filename
        except Exception as e:
            print(f"❌ 下载失败 {url}: {e}")
            return None

    # 下载所有资源
    # background_image_path = download_file(data['base_img'], "background.png")
    # audio_clip = AudioFileClip(download_file(data['bgm_audio'], "bgm_audio.mp3"))

    image_clips = []

    # 检查并加载开场视频
    openscene_path = "openscene.mp4"
    if os.path.exists(openscene_path):
        video_file_clips = VideoFileClip(openscene_path)
        image_clips.append(video_file_clips)
        print(f"✅ 成功加载开场视频: {openscene_path}")
    else:
        print(f"⚠️ 开场视频不存在: {openscene_path}")
        video_file_clips = None

    # 下载图片并生成视频片段
    for i, img_url in enumerate(data['img_lists']):
        if not img_url or img_url.strip() == "":
            print(f"⚠️ 跳过第{i}个空URL")
            continue

        img_path = download_file(img_url, f"img_{i}.png")
        if img_path:
            try:
                img_clip = ImageClip(img_path, duration=1.2)  # 每张图片显示1.2秒

                # 应用放大效果 - 在最后0.15秒快速放大
                img_clip = img_clip.with_effects_on_subclip([
                    Resize(lambda t: 1 + 10 * (t - 1.05) if t >= 1.05 else 1)
                ], start_time=0)

                image_clips.append(img_clip)
                print(f"✅ 成功处理第{i + 1}张图片: {img_path}")
            except Exception as e:
                print(f"❌ 图片处理失败 {i}: {e}")
        else:
            print(f"❌ 第{i}张图片下载失败")

    if not image_clips:
        raise ValueError("❌ 没有成功加载任何图片或视频")

    # 将所有图片片段拼接起来
    print("🎬 开始合并视频片段...")
    final_image_clips = concatenate_videoclips(image_clips, method="compose")
    print(f"✅ 视频合并完成，总时长: {final_image_clips.duration:.2f}秒")

    # 处理音频
    try:
        # 尝试下载背景音乐
        bgm_path = None
        if 'bgm_audio' in data and data['bgm_audio']:
            bgm_path = download_file(data['bgm_audio'], "bgm_audio.mp3")

        # 备用本地背景音乐
        local_bgm_path = "bgm.mp3"

        audio_clips = []

        # 添加开场视频的音频
        if video_file_clips and video_file_clips.audio:
            audio_clips.append(video_file_clips.audio)
            print("✅ 添加开场视频音频")

        # 添加背景音乐
        if bgm_path and os.path.exists(bgm_path):
            audio_clips.append(AudioFileClip(bgm_path))
            print(f"✅ 添加下载的背景音乐: {bgm_path}")
        elif os.path.exists(local_bgm_path):
            audio_clips.append(AudioFileClip(local_bgm_path))
            print(f"✅ 添加本地背景音乐: {local_bgm_path}")
        else:
            print("⚠️ 没有找到背景音乐文件")

        # 合成音频
        if audio_clips:
            final_audio = concatenate_audioclips(audio_clips)
            print("✅ 音频合成完成")

            # 音频与视频时长同步
            if final_audio.duration > final_image_clips.duration:
                final_audio = final_audio.subclipped(0, final_image_clips.duration)
                print(f"🔧 音频裁剪到视频长度: {final_image_clips.duration:.2f}秒")
            else:
                # 若视频时长超过音频时长，则重复音频直到覆盖整个视频长度
                while final_audio.duration < final_image_clips.duration:
                    remaining_duration = final_image_clips.duration - final_audio.duration
                    additional_audio = final_audio.subclipped(0, min(final_audio.duration, remaining_duration))
                    final_audio = concatenate_audioclips([final_audio, additional_audio])
                print(f"🔧 音频延长到视频长度: {final_image_clips.duration:.2f}秒")

            # 添加音频到视频
            final_video = final_image_clips.with_audio(final_audio)
        else:
            final_video = final_image_clips
            print("⚠️ 没有音频，输出静音视频")

    except Exception as e:
        print(f"❌ 音频处理失败: {e}")
        final_video = final_image_clips

    # 输出最终视频
    out_path = os.path.join(project_path, "final_video.mp4")
    print("🎬 开始输出视频文件...")

    # 使用更稳定的编码参数
    final_video.write_videofile(
        out_path,
        codec="libx264",
        fps=24,
        audio_codec="aac",
        temp_audiofile=os.path.join(project_path, "temp-audio.m4a"),
        remove_temp=True
    )

    print(f"✅ 视频已生成：{out_path}")

    # 🔥 关键修改：返回生成的视频路径
    return out_path


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
    result_path = trans_videos_clothes_fast_change(data)
    print(f"返回的视频路径: {result_path}")