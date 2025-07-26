import os
from moviepy import AudioFileClip, ImageClip, concatenate_videoclips, TextClip, CompositeVideoClip, \
    concatenate_audioclips, VideoFileClip, ColorClip
import uuid

from config import get_user_data_dir

# 加载json数据（这里直接用字典代替）
data1 = {
    "audio_list": [
        "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7468512265151741979_063f07d2-4f2f-49d7-9691-8ad707b97b02.mp3?lk3s=da27ec82&x-expires=1745090947&x-signature=yPyZB8D5c%2Fsh7HYH%2F8%2BtbRij7jU%3D",
        "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7468512265151741979_c03c8d8a-d75f-4885-9e5c-9c4f71fa0ac5.mp3?lk3s=da27ec82&x-expires=1745090950&x-signature=bm93pFPuVzhaBJ2UFkzXxjcrzes%3D",
        "https://lf9-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7468512265151741979_2cf5d342-0927-4194-93fa-f280febf2fea.mp3?lk3s=da27ec82&x-expires=1745090953&x-signature=%2B5q024zBrjQEePmB1UKLz%2BZTNRo%3D",
        "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7468512265151741979_4080dabc-fb8b-46a9-8785-925cb3d817c8.mp3?lk3s=da27ec82&x-expires=1745090957&x-signature=sErw4fWe0NM2PFbA8%2Buo8Q%2BUYLU%3D",
        "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7468512265151741979_8b43484e-df55-4762-aefc-341b0113e622.mp3?lk3s=da27ec82&x-expires=1745090959&x-signature=gPRkorS8paELv3vU0NkeQg13KdA%3D",
        "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7468512265151741979_6220de31-368e-410e-8869-4d1ca745ee89.mp3?lk3s=da27ec82&x-expires=1745090962&x-signature=LNwy7314ffo%2BAowxM30%2B4at2%2Fwg%3D"
    ],
    "duration_list": [
        17520000,
        23544000,
        15408000,
        22944000,
        8736000,
        18216000
    ],
    "image_list": [
        "https://s.coze.cn/t/knH-_miAwVQ/",
        "https://s.coze.cn/t/aaza4S3oq6g/",
        "https://s.coze.cn/t/WqH2Wos4tnU/",
        "https://s.coze.cn/t/OOohifF6J2g/",
        "https://s.coze.cn/t/Kq1HiwGDjgI/",
        "https://s.coze.cn/t/VA2Mirnl2wY/"
    ],
    "list": [
        {
            "cap": "中国古典服装是国学宝库中一颗璀璨明珠，承载着深厚文化内涵与传统审美。它不仅是遮体御寒之物，更反映着不同时代的社会风貌、礼仪制度和价值观念。",
            "desc": "画面渐亮，展现一张古朴的书桌，桌上摊开一本线装古籍，旁边放着一支毛笔和一方砚台。镜头慢慢拉近古籍，古籍上绘有各种古典服装的图案。",
            "desc_promopt": "Prompt : 采用传统工笔技法绘制，在仿古宣纸纹理背景上呈现具有东方韵味的简逸场景。以墨色骨法勾勒古籍、书桌、毛笔和砚台的轮廓，线条蕴含书法笔意，施以丹青设色之法，着朱砂、石青、赭黄等传统矿物色于古朴物件之上。背景融入水墨氤氲的祥云纹样，画面四隅点缀金石篆刻印章与梅花小景，整体营造出墨彩交融、文气盎然的古典美学意境. 画面为一张古朴书桌，桌上摊开绘有古典服装图案的线装古籍，旁边有毛笔和砚台",
            "story_name": "古典服装开篇"
        },
        {
            "cap": "春秋战国时期流行深衣，《礼记·深衣》记载：'制十有二幅，以应十二月；袂圜以应规，曲袷如矩以应方。'深衣上下连属，象征天人合一、恢宏大度、公平正直和包容万物的东方美德。",
            "desc": "场景切换至古代学堂，夫子站在讲台上，手持竹简讲解，台下学生们认真聆听。画面中出现几位身着深衣的学生走动，深衣上下连属，线条流畅。",
            "desc_promopt": "Prompt : 采用传统工笔技法绘制，在仿古宣纸纹理背景上呈现具有东方韵味的简逸场景。以墨色骨法勾勒夫子、学生和深衣的轮廓，线条蕴含书法笔意，施以丹青设色之法，着朱砂、石青、赭黄等传统矿物色于素衣之上。人物造型取法汉代画像石之简朴动态，背景融入水墨氤氲的祥云纹样，画面四隅点缀金石篆刻印章与梅花小景，整体营造出墨彩交融、文气盎然的古典美学意境. 画面为古代学堂，夫子讲学，身着深衣的学生走动",
            "story_name": "春秋战国深衣"
        },
        {
            "cap": "赵武灵王推行'胡服骑射'，让士兵着短衣、束皮带、用带钩、穿皮靴，利于骑射活动，这一变革体现了对不同文化的包容与融合。",
            "desc": "画面来到战场，赵武灵王身着短衣、束皮带、用带钩、穿皮靴，骑在战马上指挥士兵操练骑射。士兵们也都穿着同样的胡服，动作整齐划一。",
            "desc_promopt": "Prompt : 采用传统工笔技法绘制，在仿古宣纸纹理背景上呈现具有东方韵味的简逸场景。以墨色骨法勾勒赵武灵王、士兵和战马的轮廓，线条蕴含书法笔意，施以丹青设色之法，着朱砂、石青、赭黄等传统矿物色于胡服之上。人物造型取法汉代画像石之简朴动态，背景融入水墨氤氲的祥云纹样，画面四隅点缀金石篆刻印章与梅花小景，整体营造出墨彩交融、文气盎然的古典美学意境. 画面为战场，赵武灵王骑在马上指挥穿胡服的士兵操练骑射",
            "story_name": "胡服骑射变革"
        },
        {
            "cap": "唐朝是中国古典服装发展的鼎盛时期，女装款式多样，有襦裙、半臂等。当时社会开放，女性服饰色彩鲜艳、图案精美。杨贵妃喜爱华丽服饰，其着装引领时尚潮流，展现出唐朝的繁荣昌盛和自信包容。",
            "desc": "场景转换到唐朝的宫廷花园，杨贵妃身着华丽的襦裙、半臂，色彩鲜艳，图案精美，在花丛中漫步，周围有宫女陪伴。",
            "desc_promopt": "Prompt : 采用传统工笔技法绘制，在仿古宣纸纹理背景上呈现具有东方韵味的简逸场景。以墨色骨法勾勒杨贵妃、宫女和花园景色的轮廓，线条蕴含书法笔意，施以丹青设色之法，着朱砂、石青、赭黄等传统矿物色于华丽服饰之上。人物造型取法汉代画像石之简朴动态，背景融入水墨氤氲的祥云纹样，画面四隅点缀金石篆刻印章与梅花小景，整体营造出墨彩交融、文气盎然的古典美学意境. 画面为唐朝宫廷花园，杨贵妃身着华丽女装漫步，周围有宫女陪伴",
            "story_name": "唐朝女装风采"
        },
        {
            "cap": "而宋代服装则趋于保守，强调端庄、儒雅，体现了理学对社会生活的影响。",
            "desc": "画面呈现宋代的书院，书生们穿着色调淡雅、款式端庄的服装，在书院中读书、讨论。",
            "desc_promopt": "Prompt : 采用传统工笔技法绘制，在仿古宣纸纹理背景上呈现具有东方韵味的简逸场景。以墨色骨法勾勒书生和书院的轮廓，线条蕴含书法笔意，施以丹青设色之法，着朱砂、石青、赭黄等传统矿物色于淡雅服装之上。人物造型取法汉代画像石之简朴动态，背景融入水墨氤氲的祥云纹样，画面四隅点缀金石篆刻印章与梅花小景，整体营造出墨彩交融、文气盎然的古典美学意境. 画面为宋代书院，书生们穿着端庄服装读书讨论",
            "story_name": "宋代保守服装"
        },
        {
            "cap": "中国古典服装蕴含着丰富的国学智慧，它教会我们尊重传统、包容多元，在当代生活中，我们可从古典服装中汲取灵感，提升个人修养与审美，传承中华民族的文化基因。",
            "desc": "画面回到现代，一位年轻人在博物馆里看着古典服装的展品，若有所思。随后画面切换至年轻人穿着融入古典元素的现代服装，自信地走在街头。",
            "desc_promopt": "Prompt : 采用传统工笔技法绘制，在仿古宣纸纹理背景上呈现具有东方韵味的简逸场景。以墨色骨法勾勒年轻人、博物馆展品和现代街道的轮廓，线条蕴含书法笔意，施以丹青设色之法，着朱砂、石青、赭黄等传统矿物色于服装和场景之上。人物造型取法汉代画像石之简朴动态，背景融入水墨氤氲的祥云纹样，画面四隅点缀金石篆刻印章与梅花小景，整体营造出墨彩交融、文气盎然的古典美学意境. 画面先为年轻人在博物馆看古典服装展品，后为年轻人穿融入古典元素的现代服装走在街头",
            "story_name": "当代传承启示"
        }
    ]
}


def get_trans_video_sinology(input: dict) -> str:
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

    # 下载所有音频资源
    audio_clips = []
    for i, audio_url in enumerate(input['audio_list']):
        audio_path = download_file(audio_url, f"audio_{i}.mp3")
        if audio_path:
            audio_clips.append(AudioFileClip(audio_path))

    # 🔥 修复图片处理逻辑
    video_clips = []

    # 标准视频尺寸
    VIDEO_WIDTH = 1920
    VIDEO_HEIGHT = 1080

    for i, (img_url, duration_ms, item) in enumerate(zip(input['image_list'], input['duration_list'], input['list'])):
        duration_seconds = duration_ms / 1000000.0

        # 处理背景图片
        background_clip = None
        if img_url and img_url.strip():
            img_path = download_file(img_url, f"img_{i}.png")
            if img_path:
                try:
                    # 🔥 修复：保持图片比例的同时适配屏幕
                    img_clip = ImageClip(img_path)

                    # 计算缩放比例，确保图片完全显示
                    img_w, img_h = img_clip.size
                    scale_w = VIDEO_WIDTH / img_w
                    scale_h = VIDEO_HEIGHT / img_h
                    scale = min(scale_w, scale_h)  # 使用较小的缩放比例，确保图片完全显示

                    # 缩放图片
                    scaled_img = img_clip.resized(scale)

                    # 创建黑色背景
                    black_bg = ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=(0, 0, 0))

                    # 将缩放后的图片居中放置在黑色背景上
                    background_clip = CompositeVideoClip([
                        black_bg,
                        scaled_img.with_position('center')
                    ], size=(VIDEO_WIDTH, VIDEO_HEIGHT)).with_duration(duration_seconds)

                    print(f"✅ 成功加载图片 {i}: {img_path}, 原尺寸: {img_w}x{img_h}, 缩放比例: {scale:.2f}")
                except Exception as e:
                    print(f"❌ 图片处理失败 {i}: {e}")
                    background_clip = None

        # 如果没有背景图片或加载失败，创建深灰色背景
        if background_clip is None:
            print(f"⚠️ 第{i}个片段使用默认背景")
            background_clip = ColorClip(
                size=(VIDEO_WIDTH, VIDEO_HEIGHT),
                color=(20, 20, 20),  # 更深的灰色
                duration=duration_seconds
            )

        # 🔥 修复字幕处理 - 确保不超出边界
        caption = item['cap']

        # 改进文本分割 - 考虑长度限制
        max_chars_per_line = 40  # 每行最大字符数
        lines = []

        if len(caption) <= max_chars_per_line:
            lines = [caption]
        elif len(caption) <= max_chars_per_line * 2:
            # 两行文本的智能分割
            split_chars = ['。', '，', '；', '！', '？', '、']
            best_split = len(caption) // 2

            # 寻找最佳分割点
            for char in split_chars:
                positions = [i for i, c in enumerate(caption) if c == char]
                if positions:
                    mid_pos = len(caption) // 2
                    closest_pos = min(positions, key=lambda x: abs(x - mid_pos))
                    if abs(closest_pos - mid_pos) <= 10:  # 在合理范围内
                        best_split = closest_pos + 1
                        break

            line1 = caption[:best_split].strip()
            line2 = caption[best_split:].strip()

            # 如果任一行过长，强制分割
            if len(line1) > max_chars_per_line:
                line1 = line1[:max_chars_per_line - 1] + "..."
            if len(line2) > max_chars_per_line:
                line2 = line2[:max_chars_per_line - 1] + "..."

            lines = [line1, line2]
        else:
            # 超长文本，分成多行或截断
            lines = [caption[:max_chars_per_line - 1] + "...",
                     caption[max_chars_per_line:max_chars_per_line * 2 - 1] + "..."]

        # 创建字幕 - 调整位置确保在安全区域内
        txt_clips = []
        for idx, line in enumerate(lines):
            if line.strip():
                # 调整垂直位置，确保在视频边界内
                v_pos = 0.75 + (idx * 0.08)  # 从75%位置开始，每行间隔8%
                if v_pos > 0.9:  # 如果超过90%，调整到安全位置
                    v_pos = 0.9 - (len(lines) - 1 - idx) * 0.08

                txt_clip = (TextClip('微软雅黑.ttf', line,
                                     font_size=32,  # 稍微减小字体
                                     color='white',
                                     stroke_color='black',
                                     stroke_width=3,
                                     size=(VIDEO_WIDTH - 100, None),  # 限制文本宽度，留边距
                                     method='caption')  # 自动换行
                            .with_duration(duration_seconds)
                            .with_position(('center', v_pos), relative=True))
                txt_clips.append(txt_clip)

        # 🔥 修复：组合背景和字幕
        if txt_clips:
            final_clip = CompositeVideoClip([background_clip] + txt_clips, size=(VIDEO_WIDTH, VIDEO_HEIGHT))
        else:
            final_clip = background_clip

        video_clips.append(final_clip)
        print(f"✅ 完成第{i + 1}个片段处理，时长: {duration_seconds:.2f}秒")

    # 🔥 修复：使用method="compose"进行无缝拼接
    print("🎬 开始合并视频片段...")
    final_video = concatenate_videoclips(video_clips, method="compose")
    print(f"✅ 视频合并完成，总时长: {final_video.duration:.2f}秒")

    # 处理音频
    if audio_clips:
        print("🎵 开始处理音频...")
        final_audio = concatenate_audioclips(audio_clips)

        # 音频与视频时长同步
        if final_audio.duration > final_video.duration:
            final_audio = final_audio.subclipped(0, final_video.duration)
            print(f"🔧 音频裁剪到视频长度: {final_video.duration:.2f}秒")
        elif final_audio.duration < final_video.duration:
            # 如果音频较短，重复最后一段音频
            remaining_duration = final_video.duration - final_audio.duration
            if audio_clips and remaining_duration > 0:
                additional_audio = audio_clips[-1].subclipped(0, min(audio_clips[-1].duration, remaining_duration))
                final_audio = concatenate_audioclips([final_audio, additional_audio])
                print(f"🔧 音频延长到视频长度: {final_video.duration:.2f}秒")

        # 添加音频到视频
        final_video = final_video.with_audio(final_audio)
        print("✅ 音频添加完成")
    else:
        print("⚠️ 没有可用的音频文件")

    # 输出最终视频
    output_path = os.path.join(project_path, "output.mp4")
    print("🎬 开始输出视频文件...")

    # 🔥 修复：使用更稳定的编码参数
    final_video.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=os.path.join(project_path, "temp-audio.m4a"),
        remove_temp=True
    )

    print(f"✅ 视频已生成：{output_path}")
    return output_path


if __name__ == "__main__":
    input_data = data1
    result_path = get_trans_video_sinology(input_data)
    print(f"返回的视频路径: {result_path}")