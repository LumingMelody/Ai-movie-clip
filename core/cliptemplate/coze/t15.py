import pandas as pd
from datetime import datetime
from moviepy import VideoFileClip, concatenate_videoclips
import os
import tempfile
import requests
from urllib.parse import urlparse
import oss2
import time

from core.clipgenerate.interface_function import download_file_from_url, upload_to_oss


def extract_video_highlights(
    excel_path: str,
    video_path: str,
    metrics: list = ['实时在线人数', '互动率', '关注率', '商品点击率'],
    top_n: int = 3,
    output_file: str = "output_highlights.mp4"
):
    """
    根据 Excel 中的直播数据，提取视频精彩片段并合并成一个视频。

    参数:
        excel_path: Excel 文件路径
        video_path: 原始视频路径
        metrics: 要分析的指标列表
        top_n: 每个指标提取 Top N 的时间点
        output_file: 输出视频路径
    """
    temp_files = []
    
    try:
        # 处理URL输入
        if excel_path.startswith(('http://', 'https://')):
            print(f"📥 从URL下载Excel: {excel_path}")
            excel_local = download_file_from_url(excel_path, '.xlsx')
            temp_files.append(excel_local)
            excel_path = excel_local
        
        if video_path.startswith(('http://', 'https://')):
            print(f"📥 从URL下载视频: {video_path}")
            video_local = download_file_from_url(video_path, '.mp4')
            temp_files.append(video_local)
            video_path = video_local
        
        # 1. 读取Excel数据
        df = pd.read_excel(excel_path)

        # 2. 处理百分比列（替换'-'为'0%'，处理缺失）
        percentage_cols = ['互动率', '关注率', '商品点击率']
        for col in percentage_cols:
            if col in df.columns:
                df[col] = df[col].fillna('0%').str.replace('%', '').astype(float) / 100

        # 3. 时间列处理：转换为偏移秒数
        def parse_time(t):
            return datetime.strptime(t, "%Y/%m/%d %H:%M")

        first_time = parse_time(df.iloc[0]['时间'])
        df['偏移秒数'] = df['时间'].apply(lambda x: (parse_time(x) - first_time).total_seconds())

        # 4. 提取关键时间点
        key_times = []

        for metric in metrics:
            if metric not in df.columns:
                print(f"警告：Excel 中不存在列：{metric}")
                continue

            # 提取 Top N 时间点
            top_times = df.nlargest(top_n, metric)['偏移秒数'].tolist()
            key_times.extend(top_times)

        # 去重 + 排序
        key_times = sorted(list(set(key_times)))
        print(f"提取的关键时间点：{key_times}")

        # 5. 视频剪辑部分
        clips = []

        video=VideoFileClip(video_path)
        for t in key_times:
            # 以当前分钟为起点，剪辑整分钟（60秒）
            start = t
            end = t + 60

            # 确保不超过视频总时长
            if end > video.duration:
                end = video.duration

            if start < video.duration:
                clip = video.subclipped(start, end)
                clips.append(clip)

        # 合并所有片段
        if clips:
            final_clip = concatenate_videoclips(clips)
            final_clip.write_videofile(output_file)
            print(f"✅ 剪辑完成，已保存到：{os.path.abspath(output_file)}")
        else:
            print("❌ 没有找到可以剪辑的时间点。")

    except Exception as e:
        print(f"❌ 发生错误：{e}")
    
    finally:
        # 清理临时文件
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

def extract_video_highlights_from_url(
    excel_url: str,
    video_url: str,
    metrics: list = ['实时在线人数', '互动率', '关注率', '商品点击率'],
    top_n: int = 3,
    upload_to_oss_flag: bool = True
) -> dict:
    """
    从URL读取Excel和视频，处理后上传到OSS
    
    参数:
        excel_url: Excel文件的URL
        video_url: 视频文件的URL
        metrics: 要分析的指标列表
        top_n: 每个指标提取 Top N 的时间点
        upload_to_oss_flag: 是否上传到OSS
    
    返回:
        dict: 包含处理结果的字典
    """
    temp_files = []
    
    try:
        print(f"📥 开始下载Excel文件: {excel_url}")
        excel_local = download_file_from_url(excel_url, '.xlsx')
        temp_files.append(excel_local)
        print(f"✅ Excel下载完成: {excel_local}")
        
        print(f"📥 开始下载视频文件: {video_url}")
        video_local = download_file_from_url(video_url, '.mp4')
        temp_files.append(video_local)
        print(f"✅ 视频下载完成: {video_local}")
        
        # 生成输出文件名
        timestamp = int(time.time())
        output_file = f"highlights_{timestamp}.mp4"
        
        # 处理视频
        print("🎬 开始处理视频...")
        extract_video_highlights(
            excel_path=excel_local,
            video_path=video_local,
            metrics=metrics,
            top_n=top_n,
            output_file=output_file
        )
        
        result = {
            "status": "success",
            "output_file": output_file,
            "message": "视频处理成功"
        }
        
        # 上传到OSS
        if upload_to_oss_flag and os.path.exists(output_file):
            print("☁️ 开始上传到OSS...")
            try:
                oss_url = upload_to_oss(output_file)
                result["oss_url"] = oss_url
                result["message"] = f"视频处理成功并已上传到OSS"
                print(f"✅ 上传成功: {oss_url}")
                
                # 删除本地输出文件
                os.remove(output_file)
            except Exception as e:
                print(f"⚠️ OSS上传失败: {str(e)}")
                result["oss_error"] = str(e)
        
        return result
        
    except Exception as e:
        print(f"❌ 处理失败: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }
    
    finally:
        # 清理临时文件
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    print(f"🗑️ 已清理临时文件: {temp_file}")
                except:
                    pass


if __name__ == "__main__":
    # 测试URL方式
    test_excel_url = "https://example.com/test.xlsx"
    test_video_url = "https://example.com/test.mp4"
    
    # result = extract_video_highlights_from_url(
    #     excel_url=test_excel_url,
    #     video_url=test_video_url,
    #     metrics=['实时在线人数', '互动率'],
    #     top_n=2
    # )
    # print(f"处理结果: {result}")
    
    # 测试本地文件
    # excel_path = "test2.xlsx"
    # video_path = "7cf9fe5a73f562192db9c20494d216ff.mp4"
    # output_file = "output_highlights1.mp4"
    # 
    # extract_video_highlights(
    #     excel_path=excel_path,
    #     video_path=video_path,
    #     metrics=['实时在线人数', '互动率'],
    #     top_n=1,
    #     output_file=output_file
    # )