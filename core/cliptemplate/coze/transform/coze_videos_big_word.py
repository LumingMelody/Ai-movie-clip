import requests
from moviepy import AudioFileClip, ImageClip, concatenate_videoclips, concatenate_audioclips, CompositeAudioClip, afx
import os
import uuid

from config import get_resource_path, get_user_data_dir


# JSON数据


def trans_video_big_word(data: dict) -> str:
    project_id = str(uuid.uuid1())
    # base_project_path="projects"
    user_data_dir = get_user_data_dir()
    base_project_path = os.path.join(user_data_dir, "projects")
    project_path = os.path.join(base_project_path, project_id)
    os.makedirs(project_path, exist_ok=True)

    # 下载并处理音频文件
    audio_clips = []
    for i, audio_url in enumerate(data['mp3_urls']):
        response = requests.get(audio_url)
        audio_file_name = os.path.join(project_path, f"audio_{i}.mp3")
        with open(audio_file_name, 'wb') as f:
            f.write(response.content)
        audio_clip = AudioFileClip(audio_file_name)
        audio_clips.append(audio_clip)

    # 下载图片文件
    image_files = []
    for i, img_url in enumerate(data['images']):
        response = requests.get(img_url)
        image_file_name = os.path.join(project_path, f"img_{i}.png")
        with open(image_file_name, 'wb') as f:
            f.write(response.content)
        image_files.append(image_file_name)

    # 创建视频剪辑
    video_clips = []
    response = requests.get(data['cover'])
    cover_file_name = os.path.join(project_path, "cover.png")
    with open(cover_file_name, 'wb') as f:
        f.write(response.content)
    cover_clip = ImageClip(cover_file_name, duration=1)
    video_clips.append(cover_clip)

    for i, img_path in enumerate(image_files):
        video_clip = ImageClip(img_path, duration=data['mp3_durations'][i])
        video_clip = video_clip.with_audio(audio_clips[i])
        video_clips.append(video_clip)

    # 合并所有视频剪辑
    final_video = concatenate_videoclips(video_clips, method="compose")

    # 下载背景音乐并调整音量后添加到视频中
    response = requests.get(data['bg_audio'])

    with open(get_resource_path("bgm.mp3"), 'wb') as f:
        f.write(response.content)

    # 修复：处理背景音乐时长问题
    bgm_original = AudioFileClip(get_resource_path("bgm.mp3"))

    # 检查背景音乐时长并处理
    if bgm_original.duration < final_video.duration:
        # 背景音乐比视频短，需要循环播放
        loop_count = int(final_video.duration / bgm_original.duration) + 1
        bgm_clips = [bgm_original] * loop_count
        bgm = concatenate_audioclips(bgm_clips).subclipped(0, final_video.duration)
    else:
        # 背景音乐够长，直接裁剪
        bgm = bgm_original.subclipped(0, final_video.duration)

    # 调整背景音乐音量
    bgm = bgm.with_effects([afx.MultiplyVolume(0.2)])

    # 合成最终音频
    final_audio = CompositeAudioClip([final_video.audio, bgm])
    final_video = final_video.with_audio(final_audio)

    output_path = os.path.join(project_path, "final_video_with_bgm.mp4")
    # 输出最终视频文件
    final_video.write_videofile(output_path, fps=24)

    return output_path


if __name__ == "__main__":
    data = {
        "bg_audio": "https://p6-bot-sign.byteimg.com/tos-cn-i-v4nquku3lp/c83e7bcc87974fbbb37bf000fbb19f99.MP3~tplv-v4nquku3lp-image.image?rk3s=68e6b6b5&x-expires=1746129696&x-signature=fn9442MhacHoDfvAPi2NkiG9DPU%3D",
        "cover": "https://p9-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/33ec4072ea52470388b33f7a754742ef.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778386855&x-signature=unZllyALHr4dGX%2FMPe%2FoRLiUNTk%3D",
        "images": [
            "https://p9-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/fd3b4182a6e94a878662ea6fa15d2c48.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778386830&x-signature=fwQEzDjSJEgWGli0KZltRk2z9bo%3D",
            "https://p9-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/e1b91f2eb733483e8cc4af1a613e7d96.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778386831&x-signature=A9ndKUr3UmQbR%2BOL2wJBJ4NP%2BFs%3D",
            "https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/92e1b4a1a6124d028ddc2af7a2d523f5.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778386833&x-signature=Ye%2BDURzxSnE9I7IfLkgN3VpeGr4%3D",
            "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/b109174d2430425ab3847df0fef356e8.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778386834&x-signature=kJmKVz1jPNZcrNXAFejCqfq0v%2Fs%3D",
            "https://p9-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/05dcd54b11084eca824c62eaeb2e1868.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778386835&x-signature=F9YaTyfKZvlGUEkMli%2BufnbTbVA%3D"
        ],
        "mp3_durations": [
            13.584,
            11.16,
            9.96,
            9.888,
            8.712
        ],
        "mp3_urls": [
            "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_d94d832a-b33a-479a-a483-b6265d30d1a8.mp3?lk3s=da27ec82&x-expires=1747286439&x-signature=SaP7L2xkZTnSJ4Vk1EuGBXiHPPg%3D",
            "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_37fd3f27-ca8e-41a7-807e-b673bc00bcc0.mp3?lk3s=da27ec82&x-expires=1747286443&x-signature=%2B19SgBhPVOvzVm2TsIS49JwLZWY%3D",
            "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_cc848eec-f0a4-4f21-bb3c-0156bfdfb861.mp3?lk3s=da27ec82&x-expires=1747286447&x-signature=CHVKBRIBbg07sHdSBvwgqA5K9P4%3D",
            "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_590b9e56-d49e-4473-a07e-4bd286c79963.mp3?lk3s=da27ec82&x-expires=1747286450&x-signature=I9hCcqp5%2BIuUSrW%2BK2djO6hf7xs%3D",
            "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_7c883348-8051-494c-bcfe-cd3ada753cf9.mp3?lk3s=da27ec82&x-expires=1747286453&x-signature=eIjX6Gq9pUs9BDbSfYxr9oqSBDo%3D"
        ],
        "texts": "税务申报是企业按照规定向税务机关提交纳税信息并缴纳税款的过程。包括申报时间、申报方式、申报内容等关键要素。申报时间一般有明确规定，错过可能产生滞纳金；申报方式多样，如网上申报、上门申报；申报内容要准确完整，涵盖各类应税项目。"
    }
    trans_video_big_word(data)