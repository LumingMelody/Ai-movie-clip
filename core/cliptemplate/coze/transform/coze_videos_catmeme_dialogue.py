import requests
from moviepy import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip,concatenate_audioclips,VideoFileClip
import os
import uuid
import dashscope
import json

from config import get_user_data_dir, create_font_path

# # 设置字体路径处理函数
# def get_font_path(font_name="SimHei"):
#     """获取字体文件路径，优先使用系统字体"""
#     # 直接返回系统字体名称，避免文件不存在问题
#     return font_name


# 确保素材目录存在
materials_dir = os.path.join(get_user_data_dir(), "materials")
catmeme_folder = os.path.join(materials_dir, "Catmeme")
os.makedirs(catmeme_folder, exist_ok=True)


def get_Tongyi_response(template, content):
    """调用通义千问API获取响应"""
    messages = [
        {'role': 'system', 'content': template},
        {'role': 'user', 'content': content}
    ]
    try:
        response = dashscope.Generation.call(
            api_key="",
            model="qwen-plus",
            messages=messages,
            result_format='message',
            enable_search=True
        )
        res = response.output.choices[0].message.content
        print(res)
        return res
    except Exception as e:
        print(f"API调用失败: {e}")
        # 返回默认表情包选择
        return '{"Asays":"抱头痛苦小猫.mov","Bsays":"大声哇哇小猫.mov"}'


def choose_character(Asays: str, Bsays: str) -> str:
    """根据对话内容选择合适的表情包"""
    file_names = []

    # 确保目录存在
    if not os.path.exists(catmeme_folder):
        os.makedirs(catmeme_folder, exist_ok=True)
        print(f"创建目录: {catmeme_folder}")
        return (
            os.path.join(catmeme_folder, "抱头痛苦小猫.mov"),
            os.path.join(catmeme_folder, "大声哇哇小猫.mov")
        )

    # 获取目录中的所有文件
    for root, dirs, files in os.walk(catmeme_folder):
        for file in files:
            file_names.append(file)

    # 如果目录为空，返回默认值
    if not file_names:
        print(f"警告: {catmeme_folder} 目录为空")
        return (
            os.path.join(catmeme_folder, "抱头痛苦小猫.mov"),
            os.path.join(catmeme_folder, "大声哇哇小猫.mov")
        )

    # 调用API选择表情包
    template = '''我会给你一段对话，请根据我的角色选择合适的表情包。以json格式返回。
                ##示例
                # 示例输入
                # 示例对话：["Asays": "发票又丢啦？", "Bsays": "这次没丢呢。"]
                #示例表情包：["抱头痛苦小猫.mov","大声哇哇小猫.mov"]
                # 示例回答
                # {"Asays":"抱头痛苦小猫.mov","Bsays":"大声哇哇小猫.mov"} 
                # '''
    content = f"Asays:{Asays}\nBsays:{Bsays}\nfile_names:{file_names}"

    try:
        res = get_Tongyi_response(template, content)
        res_json = json.loads(res[res.find("{"):res.rfind("}") + 1])
    except Exception as e:
        print(f"解析表情包选择失败: {e}")
        res_json = {"Asays": "抱头痛苦小猫.mov", "Bsays": "大声哇哇小猫.mov"}

    # 确保返回的文件存在
    def check_file(file_name):
        full_path = os.path.join(catmeme_folder, file_name)
        if os.path.exists(full_path):
            return full_path
        print(f"文件不存在: {full_path}")
        return os.path.join(catmeme_folder, "抱头痛苦小猫.mov")

    return check_file(res_json.get("Asays", "抱头痛苦小猫.mov")), \
        check_file(res_json.get("Bsays", "大声哇哇小猫.mov"))


def load_character_video(video_path, duration, attempt_transparent=True):
    """
    加载角色视频，去掉阴影效果，调大猫猫尺寸

    Args:
        video_path: 视频文件路径
        duration: 持续时间
        attempt_transparent: 是否尝试透明处理
    """
    try:
        if not os.path.exists(video_path):
            print(f"文件不存在: {video_path}")
            # 创建占位符图片
            import numpy as np
            placeholder_array = np.full((380, 380, 3), [255, 200, 200], dtype=np.uint8)
            return ImageClip(placeholder_array).with_duration(duration)

        print(f"加载视频: {video_path}")

        # 方法1: 尝试带透明通道加载
        if attempt_transparent:
            try:
                video_clip = VideoFileClip(video_path, has_mask=True)
                print(f"✅ 成功加载透明视频: {video_path}")
            except Exception as e:
                print(f"⚠️ 透明加载失败: {e}，尝试普通加载")
                video_clip = VideoFileClip(video_path, has_mask=False)
        else:
            video_clip = VideoFileClip(video_path, has_mask=False)

        # 检查视频时长并裁剪
        if video_clip.duration > duration:
            video_clip = video_clip.subclipped(0, duration)
        elif video_clip.duration < duration:
            # 如果视频太短，循环播放
            loops_needed = int(duration / video_clip.duration) + 1
            video_clip = concatenate_videoclips([video_clip] * loops_needed).subclipped(0, duration)

        # 🔥 进一步调大猫猫尺寸，让它们更醒目
        video_clip = video_clip.resized(height=380)  # 从320进一步调大到380

        # 🔥 不再添加阴影效果，直接使用原视频
        print(f"✅ 去掉阴影，直接使用原视频尺寸: {video_clip.size}")

        print(f"最终视频尺寸: {video_clip.size}, 时长: {video_clip.duration}")
        return video_clip

    except Exception as e:
        print(f"❌ 加载视频失败: {video_path}, 错误: {e}")
        # 返回一个合理大小的彩色占位符
        import numpy as np
        placeholder_array = np.full((380, 380, 3), [200, 200, 255], dtype=np.uint8)
        return ImageClip(placeholder_array).with_duration(duration)



# 优化位置配置，调整猫猫位置更居中，尺寸更大
def get_enhanced_positions(video_width, video_height):
    """获取优化的位置配置，猫猫位置更居中，尺寸更大"""
    return {
        'title': ("center", 0.05),  # 标题位置 - 稍微往上
        'char_a_name': (0.15, 0.12),  # 角色A名字 - 稍微向右移动
        'char_b_name': (0.58, 0.12),  # 角色B名字 - 大幅向左移动
        'char_a_image': (0.08, 0.38),  # 角色A图像 - 向左移动，垂直稍微上移
        'char_b_image': (0.55, 0.38),  # 角色B图像 - 大幅向左移动，确保居中
        'char_a_text': (0.05, 0.22),  # 角色A文本
        'char_b_text': (0.55, 0.22),  # 角色B文本
    }


def trans_video_catmeme(data: dict):
    """生成小猫表情包对话视频 - 去掉阴影并调大猫猫版本"""

    # 验证输入数据
    if not data.get('texts') or len(data['texts']) == 0:
        raise ValueError("data['texts'] 不能为空")

    print(f"处理 {len(data['texts'])} 条对话")

    # 创建项目目录
    project_id = str(uuid.uuid1())
    base_project_path = os.path.join(get_user_data_dir(), 'projects')
    project_path = os.path.join(base_project_path, project_id)
    os.makedirs(project_path, exist_ok=True)

    print(f"项目目录: {project_path}")

    def download_file(url, local_filename):
        """下载远程文件并确保目录存在"""
        os.makedirs(project_path, exist_ok=True)
        local_filename = os.path.join(project_path, local_filename)

        try:
            print(f"开始下载: {url}")
            if url.startswith("http"):
                with requests.get(url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(local_filename, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
            print(f"下载完成: {local_filename}")
            return local_filename
        except Exception as e:
            print(f"下载失败: {e}")
            raise

    # 下载资源
    background_image_path = download_file(data['images'], "background.png")
    audio_path = download_file(data['bg_audio'], "bg_audio.mp3")

    # 常量设置
    constant_time = 3.0  # 每条对话的持续时间（秒）

    # 视频尺寸设置
    video_width = 1080
    video_height = 1920  # 9:16 竖屏比例

    # 🔥 优化背景处理，减少白色覆盖层的不透明度
    try:
        background_clip = ImageClip(background_image_path).resized((video_width, video_height))

        # 创建非常轻微的半透明覆盖层
        import numpy as np
        white_array = np.full((video_height, video_width, 3), 255, dtype=np.uint8)
        overlay = ImageClip(white_array).with_opacity(0.05)  # 进一步降到0.05，几乎不影响背景
        background_clip = CompositeVideoClip([background_clip, overlay])
        background_clip = background_clip.with_duration(constant_time * len(data['texts']))

        print("✅ 背景处理完成，添加了极轻微的半透明覆盖层")
    except Exception as e:
        print(f"⚠️ 背景处理失败: {e}")
        # 直接使用原背景图片
        background_clip = ImageClip(background_image_path).resized((video_width, video_height)).with_duration(
            constant_time * len(data['texts']))

    total_duration = constant_time * len(data['texts'])

    # 获取优化的位置配置
    positions = get_enhanced_positions(video_width, video_height)

    # 🔥 优化角色名称文本样式
    char_a_text = TextClip(
        text=data['characterA'],
        font=create_font_path(),
        font_size=45,
        color="white",
        stroke_color='black',
        stroke_width=3,
        bg_color=(0, 0, 0, 120)  # 进一步减少背景不透明度
    ).with_duration(total_duration).with_position(positions['char_a_name'], relative=True)

    char_b_text = TextClip(
        text=data['characterB'],
        font=create_font_path(),
        font_size=45,
        color="white",
        stroke_color='black',
        stroke_width=3,
        bg_color=(0, 0, 0, 120)  # 进一步减少背景不透明度
    ).with_duration(total_duration).with_position(positions['char_b_name'], relative=True)

    # 🔥 优化标题文本
    title_clip = TextClip(
        text=data['title'],
        font=create_font_path(),
        font_size=55,
        color="black",
        bg_color="yellow",
        method="caption",
        size=(800, None),
        stroke_color='white',
        stroke_width=1
    ).with_duration(total_duration).with_position(positions['title'], relative=True)

    # 创建文本和角色图像clips
    txt_a_clips = []
    txt_b_clips = []
    img_a_clips = []
    img_b_clips = []

    # 处理每条对话
    for i, text_pair in enumerate(data['texts']):
        try:
            print(f"处理第 {i + 1} 条对话: {text_pair}")
            start_time = i * constant_time

            # 验证对话数据
            if not isinstance(text_pair, dict) or 'Asays' not in text_pair or 'Bsays' not in text_pair:
                print(f"警告: 跳过无效的对话数据: {text_pair}")
                continue

            # 🔥 优化文本clips样式
            txt_a_clip = TextClip(
                text=text_pair["Asays"],
                font=create_font_path(),
                font_size=32,
                color="black",
                bg_color=(255, 255, 255, 180),  # 稍微减少文本背景不透明度
                method="caption",
                size=(400, None),
                stroke_color='blue',
                stroke_width=1
            ).with_duration(constant_time).with_start(start_time).with_position(positions['char_a_text'], relative=True)

            txt_b_clip = TextClip(
                text=text_pair["Bsays"],
                font=create_font_path(),
                font_size=32,
                color="black",
                bg_color=(255, 255, 255, 180),  # 稍微减少文本背景不透明度
                method="caption",
                size=(400, None),
                stroke_color='red',
                stroke_width=1
            ).with_duration(constant_time).with_start(start_time).with_position(positions['char_b_text'], relative=True)

            # 选择表情包
            img_a_path, img_b_path = choose_character(text_pair["Asays"], text_pair["Bsays"])
            print(f"选择的表情包: A={img_a_path}, B={img_b_path}")

            # 🔥 创建更大的角色图像clips
            char_a_img = load_character_video(img_a_path, constant_time, attempt_transparent=True)
            char_a_img = char_a_img.with_start(start_time).with_position(positions['char_a_image'], relative=True)

            char_b_img = load_character_video(img_b_path, constant_time, attempt_transparent=True)
            char_b_img = char_b_img.with_start(start_time).with_position(positions['char_b_image'], relative=True)

            # 添加到列表
            txt_a_clips.append(txt_a_clip)
            txt_b_clips.append(txt_b_clip)
            img_a_clips.append(char_a_img)
            img_b_clips.append(char_b_img)

            print(f"✅ 成功处理第 {i + 1} 条对话")

        except Exception as e:
            print(f"❌ 处理第 {i + 1} 条对话时出错: {e}")
            import traceback
            print(traceback.format_exc())
            continue

    # 检查是否有有效的clips
    if not txt_a_clips or not txt_b_clips or not img_a_clips or not img_b_clips:
        raise ValueError("没有有效的对话内容可以处理")

    print(f"创建了 {len(txt_a_clips)} 个文本A clips, {len(txt_b_clips)} 个文本B clips")
    print(f"创建了 {len(img_a_clips)} 个图像A clips, {len(img_b_clips)} 个图像B clips")

    # 🔥 重新排列clips层级，确保猫猫在最上层
    final_clips = [
        background_clip,  # 最底层：背景
        title_clip,  # 标题
        char_a_text,  # 角色名字
        char_b_text,
    ]

    # 添加文本clips（在猫猫下面）
    final_clips.extend(txt_a_clips)
    final_clips.extend(txt_b_clips)

    # 最后添加猫猫clips（最上层，最显眼）
    final_clips.extend(img_a_clips)
    final_clips.extend(img_b_clips)

    # 合成最终视频
    print("🎬 开始合成视频...")
    final_video = CompositeVideoClip(final_clips, size=(video_width, video_height)).with_duration(total_duration)

    # 处理音频
    try:
        print("🎵 处理音频...")
        audio_clip = AudioFileClip(audio_path)

        if audio_clip.duration > final_video.duration:
            audio_clip = audio_clip.subclipped(0, final_video.duration)
        else:
            loops = int(final_video.duration / audio_clip.duration) + 1
            audio_clip = concatenate_audioclips([audio_clip] * loops).subclipped(0, final_video.duration)

        final_clip = final_video.with_audio(audio_clip)
        print("✅ 音频处理完成")
    except Exception as e:
        print(f"⚠️ 处理音频失败: {e}")
        print("使用无音频输出...")
        final_clip = final_video

    # 输出最终视频
    out_path = os.path.join(project_path, "final_video.mp4")

    try:
        print(f"🎥 开始生成视频: {out_path}")
        final_clip.write_videofile(
            out_path,
            codec="libx264",
            fps=24,
            audio_codec="aac",
            threads=4,
            preset='medium',
            bitrate="3000k"
        )
        print(f"✅ 视频生成完成: {out_path}")
        return out_path
    except Exception as e:
        print(f"❌ 生成视频失败: {e}")
        import traceback
        print(traceback.format_exc())
        raise


if __name__ == "__main__":
    # 示例数据
    data = {
        "title": "税务稽查躲不过",
        "bg_audio": "https://lf6-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/9bb4ed8923d94e1990bcf5983b9c2358",
        "characterA": "稽查员",
        "characterB": "小李",
        "images": "https://s.coze.cn/t/H8lsXnVWImk/",
        "texts": [
            {"Asays": "「我们需要看一下你们\n最近的艺术品采购合同。」", "Bsays": "都在这里了，\n全是正规渠道买的！。"},
            {"Asays": "这张‘雕塑’的发票\n金额怎么这么高？", "Bsays": "那是限量版的"},
            {"Asays": "但我们发现这款‘雕塑’\n在网上卖得很便宜", "Bsays": "额。。"},
            {"Asays": "你可真行啊", "Bsays": "我们不懂…"},
            {"Asays": "你这是典型逃税！", "Bsays": "（哭）"},
        ]
    }

    try:
        trans_video_catmeme(data)
    except Exception as e:
        print(f"程序执行失败: {e}")