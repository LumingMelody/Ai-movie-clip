from moviepy import TextClip, CompositeVideoClip, ImageClip, ColorClip, concatenate_videoclips,VideoFileClip
import json
import math
import os
import uuid
from core.cliptemplate.coze.video_digital_human_easy import get_video_digital_huamn_easy_local

# 计算每个文本段落的时间
def calculate_text_durations(video_duration, text_list):
    total_chars = sum(len(text) for text in text_list)
    durations = []
    start_time = 0.0
    for text in text_list:
        char_count = len(text)
        duration = (char_count / total_chars) * video_duration
        end_time = start_time + duration
        durations.append((start_time, end_time))
        start_time = end_time
    return durations

# 创建字幕剪辑列表
def create_subtitles_clips(text_list, durations, fontsize=40, font='江西拙楷2.0.ttf', color='Yellow', stroke_color='black'):
    clips = []
    for i, text in enumerate(text_list):
        start, end = durations[i]
        txt_clip = TextClip(
            font,
            text,
            font_size=fontsize,
            
            color=color,
            stroke_color=stroke_color,
            stroke_width=1,
            size=(1000, None),
            method='caption'
        ).with_start(start).with_end(end).with_position(("center",0.7), relative=True)
        clips.append(txt_clip)
    return clips

# 创建标题剪辑
def create_title_clip(title, duration, fontsize=140, font='江西拙楷2.0.ttf', color='Yellow',stroke_color='black',bg_color=(0,0,0,30)):
    return TextClip(
        font,
        title,
        font_size=fontsize,
        stroke_color=stroke_color,
        stroke_width=5,
        color=color,
        bg_color=bg_color,
    ).with_duration(duration).with_position(("center",0.08), relative=True)




def trans_dgh_img_insert(data:dict,filepath)->str:
    # filepath="1\\2日.mp4"
    



    project_id=str(uuid.uuid1())
    base_project_path="projects"
    project_path=os.path.join(base_project_path,project_id)
    os.makedirs(project_path,exist_ok=True)

    clip=VideoFileClip(filepath)
    output_mp3=os.path.join(project_path,"output.mp3")
    clip.audio.write_audiofile(output_mp3)

    def download_file(url, local_filename):
        import requests
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            local_filename=os.path.join(project_path, local_filename)
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
        return local_filename



    # 创建图片剪辑列表
    def create_image_clips(pics, durations, text_positions):
        image_clips = []
        for i, url in enumerate(pics):
            if url=="\"\"":
                continue
            else:
                url=download_file(url, f"img_{i}.png")
            if url:
                # 图片出现在对应文本的开始时刻
                start = text_positions[i][0] if i < len(text_positions) else 0
                img_clip = ImageClip(url).resized(width=800).with_start(start).with_duration(3).with_position(("center",0.6), relative=True)
                image_clips.append(img_clip)
        return image_clips


    # 串联完整文本
    full_text = ''.join(data['text'])

    # 调用你提供的函数获取基础视频
    base_video_path=get_video_digital_huamn_easy_local(filepath,data["title"],full_text,output_mp3)
    # base_video = VideoFileClip("projects\\b1c3155a-2fb9-11f0-88f3-9de5e39342a5\\output.mp4")
    base_video = VideoFileClip(base_video_path)
    # 设置视频总时长（请根据实际情况修改）
    video_duration = base_video.duration

    # 主程序
    text_durations = calculate_text_durations(video_duration, data["text"])
    subtitle_clips = create_subtitles_clips(data["text"], text_durations)
    title_clip = [create_title_clip(data["title"], video_duration)]
    image_clips = create_image_clips(data["pics"], video_duration, text_durations)

    # 合成所有元素
    final_video = CompositeVideoClip([base_video] +image_clips +subtitle_clips +title_clip)

    output_path=os.path.join(project_path, "output_video.mp4")
    # 输出最终视频文件
    final_video.write_videofile(output_path, fps=24, codec='libx264')

    print("✅ 视频已生成：output_video.mp4")

if  __name__ == "__main__":
    data={
  "pics": [
    "https://img0.baidu.com/it/u=1414677129,166969041&fm=253&fmt=auto&app=120&f=JPEG?w=1101&h=800",
    "https://img0.baidu.com/it/u=175547649,566518480&fm=253&fmt=auto&app=120&f=JPEG?w=889&h=500",
    "https://img2.baidu.com/it/u=2096339027,403546254&fm=253&fmt=auto&app=138&f=JPEG?w=667&h=500",
    "https://img2.baidu.com/it/u=22532518,3083532290&fm=253&fmt=auto&app=138&f=JPEG?w=751&h=500",
    "http://img1.baidu.com/it/u=2994997335,1102693229&fm=253&app=138&f=JPEG?w=500&h=667",
    "https://img0.baidu.com/it/u=4215344380,3750339295&fm=253&fmt=auto&app=120&f=JPEG?w=1140&h=759",
    "http://img0.baidu.com/it/u=844424846,95604301&fm=253&app=138&f=JPEG?w=500&h=667",
    "http://img2.baidu.com/it/u=831405529,141837181&fm=253&app=138&f=JPEG?w=474&h=218",
    "https://img2.baidu.com/it/u=3850197812,278483123&fm=253&fmt=auto&app=138&f=JPEG?w=667&h=500",
    "http://img0.baidu.com/it/u=1724383772,1632210955&fm=253&app=120&f=JPEG?w=1140&h=760",
    "http://img0.baidu.com/it/u=2654062547,1769173428&fm=253&app=138&f=JPEG?w=475&h=475",
    "https://img1.baidu.com/it/u=1076544263,3446425432&fm=253&fmt=auto&app=138&f=JPEG?w=800&h=500"
  ],
  "text": [
    "实体老板为什么一定要做抖音？",
    "因为现在消费者的模式已经发生了改变",
    "以前的流量是街上逛街的人群",
    "现在的人，尤其是年轻人",
    "出去玩出去消费，都是网上先种草",
    "看好了再去线下消费",
    "如果他们在高铁上刷到的",
    "都是你对手同行的短视频",
    "那你的店就已经输了！",
    "所以，实体老板们",
    "知道该怎么做了吗？",
    "一定要去做线上引流！"
  ],
  "title": "线上引流"
}
    filepath="1\\WeChat_20250523111220.mp4"
    trans_dgh_img_insert(data,filepath)
