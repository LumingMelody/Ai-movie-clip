from moviepy import *

# 参数设置
background_images = ['1.png', '2.png', '3.png']  # 背景图片路径
text_data = [
    {
        "p_content": "企业重压如山？利润总被税负吞噬？",
        "p_title": "企业税负困境"
    },
    {
        "p_content": "一场神奇的税务筹划之旅即将开启，教你巧妙减负",
        "p_title": "税务筹划启程"
    },
    {
        "p_content": "解锁财富增长新密码！",
        "p_title": "解锁财富密码"
    }
]
fontsize_title = 50
fontsize_content = 40
color_title = "red"
color_content = "white"
interval_per_char = 0.1  # 每个字符间隔时间（秒）
pause_after_section = 0.5  # 每段之间的暂停时长
fps = 24
video_size = (1080, 1920)
blur_radius = 5  # 模糊半径
font="江西拙楷2.0.ttf"

# 创建单个段落的文字动画（标题 + 内容）
def create_section(p_title, p_content,i):
    title_clip = typing_effect(p_title, fontsize_title, color_title, interval_per_char, video_size[1] // 4+i*fontsize_title*1.5)
    content_clip = typing_effect(p_content, fontsize_content, color_content, interval_per_char, video_size[1] // 2+i*fontsize_title*1.5)

    # 标题结束之后紧接着内容开始
    content_clip = content_clip.with_start(title_clip.duration)

    # 组合标题+内容，并设定整体持续时间
    total_duration = title_clip.duration + content_clip.duration + pause_after_section
    section_clip = CompositeVideoClip([title_clip, content_clip], size=video_size).with_duration(total_duration)

    return section_clip

# 打字效果函数
def typing_effect(text, fontsize, color, interval_per_char, y_position):
    clips = []
    for i in range(1, len(text) + 1):
        txt = text[:i]
        clip = TextClip(font, txt, font_size=fontsize, color=color)
        clip = clip.with_position(('center', y_position))
        clip = clip.with_start((i - 1) * interval_per_char)
        clip = clip.with_duration(interval_per_char)
        clips.append(clip)

    composite = concatenate_videoclips(clips, method="chain")
    # composite = composite.crossfadein(interval_per_char).crossfadeout(interval_per_char)
    # composite = composite.with_duration(len(text) * interval_per_char + pause_after_section)
    return composite

# 创建背景轮换视频
def create_background_clips(max_duration):
    clips = []
    for img in background_images:
        clip = ImageClip(img).resized(height=video_size[1]).with_fps(fps).with_duration(max_duration)
        
        # 添加从下到上的移动效果
        def move_up(t):
            speed = 10  # 控制速度，数值越大速度越快
            return ('center', max(0, video_size[1] - t * speed))

        clip = clip.with_position(move_up)

        # 应用模糊效果
        clip = clip.with_effects([vfx.HeadBlur(fx=lambda t: 540, fy=lambda t: 960, radius=blur_radius, intensity=3.0)])

        clips.append(clip)
    
    # 将所有背景剪辑连接起来
    final_clip = concatenate_videoclips(clips, method='chain').with_duration(max_duration)
    return final_clip

# 主程序
if __name__ == "__main__":
    # 计算最长部分的时间
    max_duration = 0
    for item in text_data:
        section_duration = len(item["p_title"]) * interval_per_char + len(item["p_content"]) * interval_per_char + pause_after_section

        max_duration += section_duration
    i=0
    section_clips=[]
    # 创建文本部分
    for item in text_data:
        c_clip=create_section(item["p_title"], item["p_content"],i)
        section_clips.append(c_clip)
        i+=1

    # section_clips = [create_section(item["p_title"], item["p_content"]) for item in text_data]
    full_video = concatenate_videoclips(section_clips, method="compose").with_duration(max_duration)

    # 创建背景部分
    background = create_background_clips(max_duration)

    # 合成背景与文字
    final_video = CompositeVideoClip([background, full_video], size=video_size)

    # 导出
    final_video.write_videofile("moving_blurred_background.mp4", fps=fps, codec="libx264", audio=False)







