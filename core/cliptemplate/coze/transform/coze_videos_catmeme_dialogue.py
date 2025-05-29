import requests
from moviepy import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip,concatenate_audioclips,VideoFileClip
import os
import uuid
import dashscope
import json

from config import get_user_data_dir

# 设置字体路径处理函数
def get_font_path(font_name="SimHei"):
    """获取字体文件路径，优先使用系统字体"""
    # 直接返回系统字体名称，避免文件不存在问题
    return font_name


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


def trans_video_catmeme(data: dict):
    """生成小猫表情包对话视频"""
    # 创建项目目录
    project_id = str(uuid.uuid1())
    base_project_path = os.path.join(get_user_data_dir(), 'projects')
    project_path = os.path.join(base_project_path, project_id)
    os.makedirs(project_path, exist_ok=True)

    print(f"项目目录: {project_path}")

    def download_file(url, local_filename):
        """下载远程文件并确保目录存在"""
        # 确保目标目录存在
        os.makedirs(project_path, exist_ok=True)
        local_filename = os.path.join(project_path, local_filename)

        try:
            print(f"开始下载: {url}")
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

    # 创建背景图片clip
    total_duration = constant_time * len(data['texts'])
    background_clip = ImageClip(background_image_path).with_duration(total_duration)

    # 创建角色名称文本
    char_a_text = TextClip(
        text=data['characterA'],
        font=get_font_path(),
        font_size=40,
        color="white",
        stroke_color='yellow',
        stroke_width=2
    ).with_duration(total_duration)

    char_b_text = TextClip(
        text=data['characterB'],
        font=get_font_path(),
        font_size=40,
        color="white",
        stroke_color='yellow',
        stroke_width=2
    ).with_duration(total_duration)

    # 创建标题文本
    title_clip = TextClip(
        text=data['title'],
        font=get_font_path(),
        font_size=60,
        color="black",
        bg_color="yellow",
        method="caption",  # 多行文本支持
        size=(1000, None)  # 限制文本宽度
    ).with_duration(total_duration)

    # 创建文本和角色图像clips
    txt_a_clips = []
    txt_b_clips = []
    img_a_clips = []
    img_b_clips = []

    for i, text_pair in enumerate(data['texts']):
        start_time = i * constant_time

        # 创建文本clips
        txt_a_clip = TextClip(
            text=text_pair["Asays"],
            font=get_font_path(),
            font_size=36,
            color="black",
            stroke_color='yellow',
            stroke_width=1,
            method="caption",  # 多行文本支持
            size=(500, None)  # 限制文本宽度
        ).with_duration(constant_time).with_start(start_time)

        txt_b_clip = TextClip(
            text=text_pair["Bsays"],
            font=get_font_path(),
            font_size=36,
            color="black",
            stroke_color='yellow',
            stroke_width=1,
            method="caption",  # 多行文本支持
            size=(500, None)  # 限制文本宽度
        ).with_duration(constant_time).with_start(start_time)

        # 选择表情包
        img_a_path, img_b_path = choose_character(text_pair["Asays"], text_pair["Bsays"])

        # 创建角色图像clips
        try:
            char_a_img = VideoFileClip(img_a_path, has_mask=True).subclip(0, constant_time)
            char_a_img = char_a_img.resize(height=200)  # 统一图像高度
        except Exception as e:
            print(f"加载图像失败: {img_a_path}, 错误: {e}")
            # 创建一个占位图像
            char_a_img = ImageClip(os.path.join(catmeme_folder, "抱头痛苦小猫.mov")).with_duration(constant_time)
            char_a_img = char_a_img.resize(height=200)

        try:
            char_b_img = VideoFileClip(img_b_path, has_mask=True).subclip(0, constant_time)
            char_b_img = char_b_img.resize(height=200)  # 统一图像高度
        except Exception as e:
            print(f"加载图像失败: {img_b_path}, 错误: {e}")
            # 创建一个占位图像
            char_b_img = ImageClip(os.path.join(catmeme_folder, "大声哇哇小猫.mov")).with_duration(constant_time)
            char_b_img = char_b_img.resize(height=200)

        # 设置开始时间
        char_a_img = char_a_img.with_start(start_time)
        char_b_img = char_b_img.with_start(start_time)

        # 添加到列表
        txt_a_clips.append(txt_a_clip)
        txt_b_clips.append(txt_b_clip)
        img_a_clips.append(char_a_img)
        img_b_clips.append(char_b_img)

    # 合成最终视频
    final_video = CompositeVideoClip([
        background_clip,
        title_clip.set_position(("center", 0.1), relative=True),  # 标题位置
        char_a_text.set_position((0.2, 0.2), relative=True),  # 角色A名称
        char_b_text.set_position((0.7, 0.2), relative=True),  # 角色B名称

        # 角色A的对话和图像
        CompositeVideoClip([
            txt_a_clip.set_position((0.1, 0.3), relative=True)
            for txt_a_clip in txt_a_clips
        ]),

        # 角色B的对话和图像
        CompositeVideoClip([
            txt_b_clip.set_position((0.5, 0.3), relative=True)
            for txt_b_clip in txt_b_clips
        ]),

        # 角色A的表情包
        CompositeVideoClip([
            img_a_clip.set_position((0.1, 0.4), relative=True)
            for img_a_clip in img_a_clips
        ]),

        # 角色B的表情包
        CompositeVideoClip([
            img_b_clip.set_position((0.5, 0.4), relative=True)
            for img_b_clip in img_b_clips
        ])
    ]).with_duration(total_duration)

    # 处理音频
    try:
        audio_clip = AudioFileClip(audio_path)

        # 如果音频总时长超过视频时长，则裁剪音频
        if audio_clip.duration > final_video.duration:
            audio_clip = audio_clip.subclip(0, final_video.duration)
        else:
            # 若视频时长超过音频时长，则循环音频
            loops = int(final_video.duration / audio_clip.duration) + 1
            audio_clip = concatenate_audioclips([audio_clip] * loops).subclip(0, final_video.duration)

        # 添加音频到视频
        final_clip = final_video.set_audio(audio_clip)
    except Exception as e:
        print(f"处理音频失败: {e}")
        print("使用无音频输出...")
        final_clip = final_video

    # 输出最终视频
    out_path = os.path.join(project_path, "final_video.mp4")

    try:
        print(f"开始生成视频: {out_path}")
        final_clip.write_videofile(
            out_path,
            codec="libx264",
            fps=24,
            audio_codec="aac",
            threads=4,
            verbose=False,
            progress_bar=True
        )
        print(f"✅ 视频已生成: {out_path}")
        return out_path
    except Exception as e:
        print(f"生成视频失败: {e}")
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