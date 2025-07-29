import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Union
import os
import tempfile
import requests
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips
import json


class VideoHighlightClipper:
    """基于Excel观看数据提取视频高光片段"""
    
    def __init__(self):
        # 高光评分权重配置 - 根据实际数据列优化
        self.highlight_weights = {
            '实时在线人数': 0.15,
            '进入直播间人数': 0.15,
            '点赞次数': 0.20,
            '评论次数': 0.15,
            '互动率': 0.10,
            '成交人数': 0.10,
            '新增粉丝数': 0.05,
            '商品点击人数': 0.05,
            '商品曝光人数': 0.05
        }
        
        self.temp_files = []  # 追踪临时文件以便清理
    
    def _download_file(self, url: str, suffix: str = None) -> str:
        """下载文件到临时目录"""
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 创建临时文件
            if suffix is None:
                suffix = os.path.splitext(url.split('/')[-1])[1]
            
            temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
            self.temp_files.append(temp_file.name)
            
            # 下载文件
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
            
            temp_file.close()
            print(f"✅ 下载完成: {url} -> {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            print(f"❌ 下载失败 {url}: {str(e)}")
            raise
    
    def _process_input(self, input_path: str, file_type: str) -> str:
        """处理输入路径或URL"""
        if input_path.startswith(('http://', 'https://')):
            # 是URL，需要下载
            suffix = '.mp4' if file_type == 'video' else '.xlsx'
            return self._download_file(input_path, suffix)
        else:
            # 是本地路径
            if not os.path.exists(input_path):
                raise ValueError(f"文件不存在: {input_path}")
            return input_path
    
    def _parse_time(self, time_str: str) -> datetime:
        """解析时间字符串"""
        # 尝试多种时间格式
        formats = [
            "%Y/%m/%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y/%m/%d %H:%M:%S"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"无法解析时间格式: {time_str}")
    
    def _parse_percentage(self, value: str) -> float:
        """解析百分比字符串"""
        if pd.isna(value) or value == '-':
            return 0.0
        if isinstance(value, str) and '%' in value:
            try:
                return float(value.strip('%')) / 100
            except:
                return 0.0
        return float(value)
    
    def _parse_currency(self, value: str) -> float:
        """解析货币字符串"""
        if pd.isna(value) or value == '-':
            return 0.0
        if isinstance(value, str):
            # 移除货币符号和逗号
            value = value.replace('¥', '').replace(',', '').strip()
            try:
                return float(value)
            except:
                return 0.0
        return float(value)
    
    def _calculate_highlight_score(self, row: pd.Series) -> float:
        """计算单个时间点的高光分数"""
        score = 0
        
        # 实时在线人数
        if '实时在线人数' in row and pd.notna(row['实时在线人数']):
            score += float(row['实时在线人数']) * self.highlight_weights['实时在线人数']
        
        # 进入直播间人数（新增观众）
        if '进入直播间人数' in row and pd.notna(row['进入直播间人数']):
            score += float(row['进入直播间人数']) * self.highlight_weights['进入直播间人数']
        
        # 点赞次数 - 重要指标
        if '点赞次数' in row and pd.notna(row['点赞次数']):
            score += float(row['点赞次数']) * self.highlight_weights['点赞次数'] * 0.1
        
        # 评论次数
        if '评论次数' in row and pd.notna(row['评论次数']):
            score += float(row['评论次数']) * self.highlight_weights['评论次数']
        
        # 互动率 - 使用百分比解析
        if '互动率' in row:
            interaction_rate = self._parse_percentage(row['互动率'])
            score += interaction_rate * self.highlight_weights['互动率'] * 100
        
        # 成交人数
        if '成交人数' in row and pd.notna(row['成交人数']):
            score += float(row['成交人数']) * self.highlight_weights['成交人数'] * 5
        
        # 新增粉丝数
        if '新增粉丝数' in row and pd.notna(row['新增粉丝数']):
            score += float(row['新增粉丝数']) * self.highlight_weights['新增粉丝数'] * 10
        
        # 商品点击人数
        if '商品点击人数' in row and pd.notna(row['商品点击人数']):
            score += float(row['商品点击人数']) * self.highlight_weights['商品点击人数']
        
        # 商品曝光人数
        if '商品曝光人数' in row and pd.notna(row['商品曝光人数']):
            score += float(row['商品曝光人数']) * self.highlight_weights['商品曝光人数'] * 0.5
        
        return score
    
    def analyze_excel_data(self, excel_path: str) -> Tuple[pd.DataFrame, List[Dict]]:
        """分析Excel数据，返回数据框和高光片段列表"""
        # 读取Excel
        df = pd.read_excel(excel_path)
        print(f"📊 读取Excel数据: {len(df)} 行")
        
        # 解析时间
        df['timestamp'] = df['时间'].apply(self._parse_time)
        start_time = df['timestamp'].min()
        df['relative_seconds'] = (df['timestamp'] - start_time).dt.total_seconds()
        
        # 计算高光分数
        df['highlight_score'] = df.apply(self._calculate_highlight_score, axis=1)
        
        # 标准化分数
        if df['highlight_score'].max() > 0:
            df['highlight_score'] = (df['highlight_score'] / df['highlight_score'].max()) * 100
        
        # 使用滑动窗口平滑分数
        window_size = min(3, len(df))
        df['smoothed_score'] = df['highlight_score'].rolling(window=window_size, center=True).mean()
        df['smoothed_score'].fillna(df['highlight_score'], inplace=True)
        
        # 动态阈值：使用多级阈值策略
        mean_score = df['smoothed_score'].mean()
        std_score = df['smoothed_score'].std()
        
        # 首选阈值：平均值 + 0.5倍标准差
        primary_threshold = mean_score + std_score * 0.5
        # 备选阈值：平均值
        secondary_threshold = mean_score
        # 最低阈值：前30%的分数
        tertiary_threshold = df['smoothed_score'].quantile(0.7)
        
        # 尝试不同阈值识别高光片段
        for threshold_name, score_threshold in [
            ("primary", primary_threshold),
            ("secondary", secondary_threshold),
            ("tertiary", tertiary_threshold)
        ]:
            highlights = []
            in_highlight = False
            start_idx = None
            
            for idx, row in df.iterrows():
                if row['smoothed_score'] >= score_threshold:
                    if not in_highlight:
                        in_highlight = True
                        start_idx = idx
                else:
                    if in_highlight:
                        end_idx = idx - 1
                        if end_idx > start_idx:  # 确保片段有效
                            highlights.append({
                                'start_time': df.loc[start_idx, 'relative_seconds'],
                                'end_time': df.loc[end_idx, 'relative_seconds'],
                                'score': df.loc[start_idx:end_idx, 'smoothed_score'].mean(),
                                'peak_score': df.loc[start_idx:end_idx, 'smoothed_score'].max(),
                                'duration': df.loc[end_idx, 'relative_seconds'] - df.loc[start_idx, 'relative_seconds']
                            })
                        in_highlight = False
            
            # 处理最后一个片段
            if in_highlight and start_idx is not None:
                end_idx = len(df) - 1
                highlights.append({
                    'start_time': df.loc[start_idx, 'relative_seconds'],
                    'end_time': df.loc[end_idx, 'relative_seconds'],
                    'score': df.loc[start_idx:end_idx, 'smoothed_score'].mean(),
                    'peak_score': df.loc[start_idx:end_idx, 'smoothed_score'].max(),
                    'duration': df.loc[end_idx, 'relative_seconds'] - df.loc[start_idx, 'relative_seconds']
                })
            
            # 如果找到合适的高光片段，停止尝试
            if len(highlights) >= 1:
                print(f"📊 使用{threshold_name}阈值 ({score_threshold:.2f}) 发现 {len(highlights)} 个高光片段")
                break
        
        # 如果还是没有找到高光片段，选择分数最高的连续时段
        if not highlights:
            print("⚠️ 未发现明显高光片段，选择最优时段")
            # 找到最高分数的索引
            peak_idx = df['smoothed_score'].idxmax()
            # 向前后扩展形成片段
            window_size = min(len(df) // 4, 10)  # 取数据长度的1/4或10个时间点
            start_idx = max(0, peak_idx - window_size // 2)
            end_idx = min(len(df) - 1, peak_idx + window_size // 2)
            
            highlights = [{
                'start_time': df.loc[start_idx, 'relative_seconds'],
                'end_time': df.loc[end_idx, 'relative_seconds'],
                'score': df.loc[start_idx:end_idx, 'smoothed_score'].mean(),
                'peak_score': df.loc[peak_idx, 'smoothed_score'],
                'duration': df.loc[end_idx, 'relative_seconds'] - df.loc[start_idx, 'relative_seconds']
            }]
        
        # 按分数排序
        highlights.sort(key=lambda x: x['peak_score'], reverse=True)
        
        print(f"🎯 最终选择 {len(highlights)} 个片段")
        return df, highlights
    
    def select_best_highlights(self, highlights: List[Dict], target_duration: int = 30,
                             min_clip_duration: int = 3, max_clips: int = 5) -> List[Dict]:
        """选择最佳高光片段组合"""
        selected = []
        total_duration = 0
        
        for highlight in highlights:
            # 确保最小片段长度
            clip_duration = highlight['end_time'] - highlight['start_time']
            
            if clip_duration < min_clip_duration:
                # 扩展片段
                center = (highlight['start_time'] + highlight['end_time']) / 2
                highlight['start_time'] = max(0, center - min_clip_duration / 2)
                highlight['end_time'] = center + min_clip_duration / 2
                clip_duration = min_clip_duration
            
            # 检查是否超过目标时长或片段数
            if total_duration + clip_duration > target_duration or len(selected) >= max_clips:
                # 尝试截断最后一个片段
                remaining = target_duration - total_duration
                if remaining >= min_clip_duration and len(selected) < max_clips:
                    highlight['end_time'] = highlight['start_time'] + remaining
                    selected.append(highlight)
                break
            
            selected.append(highlight)
            total_duration += clip_duration
        
        # 按时间顺序排序
        selected.sort(key=lambda x: x['start_time'])
        
        print(f"📌 选择了 {len(selected)} 个片段，总时长: {total_duration:.1f}秒")
        return selected
    
    def clip_video(self, video_path: str, excel_path: str, 
                   output_path: str = None, target_duration: int = 30) -> str:
        """
        主函数：基于Excel数据剪辑视频高光片段
        
        Args:
            video_path: 视频文件路径或URL
            excel_path: Excel文件路径或URL
            output_path: 输出文件路径（可选）
            target_duration: 目标视频时长（秒）
            
        Returns:
            输出视频文件路径
        """
        try:
            print("🎬 开始处理视频高光剪辑")
            
            # 处理输入文件
            video_file = self._process_input(video_path, 'video')
            excel_file = self._process_input(excel_path, 'excel')
            
            # 分析Excel数据
            df, highlights = self.analyze_excel_data(excel_file)
            
            if not highlights:
                print("⚠️ 未发现明显的高光片段，将使用评分最高的时段")
                # 使用评分最高的连续片段
                top_idx = df['smoothed_score'].idxmax()
                window = min(10, len(df) // 2)  # 窗口大小
                start_idx = max(0, top_idx - window // 2)
                end_idx = min(len(df) - 1, top_idx + window // 2)
                
                highlights = [{
                    'start_time': df.loc[start_idx, 'relative_seconds'],
                    'end_time': df.loc[end_idx, 'relative_seconds'],
                    'score': df.loc[start_idx:end_idx, 'smoothed_score'].mean(),
                    'peak_score': df.loc[top_idx, 'smoothed_score'],
                    'duration': df.loc[end_idx, 'relative_seconds'] - df.loc[start_idx, 'relative_seconds']
                }]
            
            # 选择最佳片段
            selected_highlights = self.select_best_highlights(highlights, target_duration)
            
            # 加载视频
            video = VideoFileClip(video_file)
            video_duration = video.duration
            
            # 提取片段
            clips = []
            for i, highlight in enumerate(selected_highlights):
                # 添加缓冲时间
                start = max(0, highlight['start_time'] - 1)
                end = min(video_duration, highlight['end_time'] + 1)
                
                # 确保时间有效
                if start >= video_duration:
                    print(f"⚠️ 片段 {i+1} 超出视频范围，跳过")
                    continue
                
                if end > video_duration:
                    end = video_duration
                
                if end <= start:
                    print(f"⚠️ 片段 {i+1} 时间无效，跳过")
                    continue
                
                # 提取片段
                clip = video.subclipped(start, end)
                clips.append(clip)
                print(f"✂️ 提取片段 {i+1}: {start:.1f}s - {end:.1f}s (分数: {highlight['score']:.1f})")
            
            if not clips:
                raise ValueError("没有有效的视频片段可以提取")
            
            # 合并片段
            final_video = concatenate_videoclips(clips)
            
            # 生成输出路径
            if output_path is None:
                # 使用配置的用户数据目录（ikun目录）
                import sys
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                import config
                output_dir = config.get_user_data_dir()
                os.makedirs(output_dir, exist_ok=True)
                output_filename = f"highlight_{os.path.basename(video_file)}"
                output_path = os.path.join(output_dir, output_filename)
                print(f"📁 输出目录: {output_dir}")
                print(f"📄 输出文件: {output_filename}")
            
            # 导出视频
            print(f"💾 导出视频: {output_path}")
            final_video.write_videofile(output_path, codec='libx264', audio_codec='aac')
            
            # 清理资源
            video.close()
            final_video.close()
            
            print(f"✅ 视频剪辑完成: {output_path}")
            
            # 返回相对路径（只返回文件名）
            relative_path = os.path.basename(output_path)
            print(f"📤 返回相对路径: {relative_path}")
            return relative_path
            
        except Exception as e:
            print(f"❌ 处理失败: {str(e)}")
            raise
        finally:
            # 清理临时文件
            self._cleanup()
    
    def _cleanup(self):
        """清理临时文件"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"🧹 清理临时文件: {temp_file}")
            except Exception as e:
                print(f"⚠️ 清理文件失败: {temp_file}, {str(e)}")
        self.temp_files.clear()


def process_video_highlight_clip(video_source: str, excel_source: str, 
                                target_duration: int = 30, output_path: str = None) -> str:
    """
    接口函数：处理视频高光剪辑
    
    Args:
        video_source: 视频文件路径或URL
        excel_source: Excel文件路径或URL
        target_duration: 目标视频时长（秒）
        output_path: 输出路径（可选）
        
    Returns:
        输出文件的相对路径（文件名）
    """
    try:
        clipper = VideoHighlightClipper()
        result_path = clipper.clip_video(
            video_path=video_source,
            excel_path=excel_source,
            output_path=output_path,
            target_duration=target_duration
        )
        
        print(f"🎬 处理成功，返回文件名: {result_path}")
        return result_path
        
    except Exception as e:
        print(f"❌ process_video_highlight_clip 失败: {str(e)}")
        raise


if __name__ == "__main__":
    # 测试代码
    print("🔧 视频高光剪辑测试")
    
    # 本地测试
    video_path = "test.mp4"
    excel_path = "test2.xlsx"
    
    # URL测试示例
    # video_path = "https://example.com/video.mp4"
    # excel_path = "https://example.com/data.xlsx"
    
    try:
        result = process_video_highlight_clip(
            video_source=video_path,
            excel_source=excel_path,
            target_duration=30
        )
        
        print(f"\n📋 处理结果: 成功")
        print(f"📄 输出文件: {result}")
    except Exception as e:
        print(f"\n❌ 处理失败: {str(e)}")