import numpy as np
from moviepy import ImageClip,VideoClip,CompositeVideoClip,concatenate_videoclips,ColorClip,VideoFileClip,TextClip,vfx
from math import sqrt, sin, cos, radians
import math
import os
import cv2
import random
from scipy.ndimage import gaussian_filter
from PIL import Image

def ease_in_out_quad(t):
    """平滑加速和减速"""
    return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2

def ease_in_quad(t):
    """加速开始"""
    return t * t

def ease_out_quad(t):
    """减速结束"""
    return 1 - (1 - t) ** 2

def linear(t):
    """线性运动（无缓动）"""
    return t


def calculate_scale_for_rotation(angle):
    """根据旋转角度计算缩放因子以避免黑边"""
    angle_rad = radians(angle)
    return 1 / (cos(angle_rad) + abs(sin(angle_rad)))

# # 假设ease_in_out_quad已经定义
# def ease_in_out_quad(t):
#     if t < 0.5:
#         return 2 * t * t
#     else:
#         return -1 + (4 - 2 * t) * t


##TODO: 需要优化按照固定点位缩放，转灰度图用opencv进行定位，然后用人脸面积找到最大的那张脸，以那张脸为中心缩放，另起一个函数zoom_in_face
def zoom_in(clip: VideoClip, duration=2, intensity=0.3, easing=ease_in_out_quad):
    """
    创建一个从中心逐渐放大的视频效果，避免画面拉伸或旋转。
    
    参数:
        clip (VideoClip): 输入视频剪辑。
        duration (float): 动画持续时间（秒）。
        intensity (float): 放大强度，如 0.5 表示放大到 1.5 倍。
        easing (function): 插值函数，输入 [0,1] 输出 [0,1]
        
    返回:
        VideoClip: 放大动画视频。
    """
    w, h = clip.size
    start_scale = 1.0
    end_scale = 1.0 + intensity

    # 预放大到最大尺寸，避免黑边
    # pre_zoomed_clip = clip.with_effects([vfx.Resize(end_scale)])
    pre_zoomed_clip = clip
    # 定义每帧的缩放函数
    def scale_func(t):
        if t >= duration:
            return end_scale
        progress = t / duration
        scale_progress = easing(progress)
        return start_scale + (end_scale - start_scale) * scale_progress

    # 动态缩放剪辑，设置固定大小并居中显示
    animated_clip = (
        pre_zoomed_clip
        .with_effects([vfx.Resize(lambda t: scale_func(t))])
        .with_position(("center", "center"))  # 确保始终居中
    )

    # 创建一个固定大小的合成背景，防止画面变形
    final_clip = CompositeVideoClip(
        [animated_clip],
        size=clip.size,
        bg_color=(0, 0, 0)  # 可选黑底，也可以透明
    ).with_duration(duration)

    return final_clip


def zoom_out(clip: VideoClip, duration=2, intensity=0.3, easing=ease_in_out_quad):
    """
    创建一个从原始大小逐渐缩小的视频效果，避免画面拉伸或错位。
    
    参数:
        clip (VideoClip): 输入视频剪辑。
        duration (float): 动画持续时间（秒）。
        intensity (float): 缩小强度，如 0.3 表示缩小到 0.7 倍。
        easing (function): 插值函数，输入 [0,1] 输出 [0,1]
        
    返回:
        VideoClip: 缩小动画视频。
    """
    w, h = clip.size
    start_scale = 1.0
    end_scale = 1.0 - intensity

    # 预放大以防止缩小时内容超出边界（可选）
    pre_scaled_clip = clip.with_effects([vfx.Resize(1/end_scale)])

    def scale_func(t):
        if t >= duration:
            return end_scale
        progress = t / duration
        scale_progress = easing(progress)
        return start_scale + (end_scale - start_scale) * scale_progress

    animated_clip = (
        pre_scaled_clip
        .with_effects([vfx.Resize(lambda t: scale_func(t))])
        .with_position(("center", "center"))  # 确保始终居中
    )

    final_clip = CompositeVideoClip(
        [animated_clip],
        size=clip.size,
        bg_color=(0, 0, 0)  # 可选黑底，也可以透明背景
    ).with_duration(duration)

    return final_clip

def pan(clip: VideoClip, duration=2, intensity=100, direction='left', easing=ease_in_out_quad):
    """
    创建一个带有平移动画的视频效果，支持上下左右方向。
    
    参数:
        clip (VideoClip): 输入视频剪辑。
        duration (float): 动画持续时间（秒）。
        intensity (int/float): 平移距离（像素）。
        direction (str): 平移方向，支持 'left', 'right', 'up', 'down'。
        easing (function): 插值函数，输入 [0,1] 输出 [0,1]
        
    返回:
        VideoClip: 带平移动画的视频剪辑。
    """
    w, h = clip.size
    original_size = (w, h)

    # 预放大以避免平移时露出黑边
    zoom_scale = 1.5  # 可根据需要调整
    pre_zoomed_clip = clip.resized(zoom_scale)

    # 获取放大后的真实尺寸
    zoomed_w, zoomed_h = pre_zoomed_clip.size

    def position_func(t):
        if t > duration:
            return ("center", "center")
        progress = easing(t / duration)
        offset = intensity * progress

        if direction == 'left':
            x = -offset
        elif direction == 'right':
            x = offset
        elif direction == 'up':
            x = 0
            y = -offset
            return ("center", y)
        elif direction == 'down':
            x = 0
            y = offset
            return ("center", y)
        else:
            x = 0

        return (x, "center")

    animated_clip = (
        pre_zoomed_clip
        .with_position(position_func)  # 设置动态位置
        .with_duration(duration)
    )

    # 固定输出分辨率为原视频大小
    final_clip = CompositeVideoClip(
        [animated_clip],
        size=original_size,
        bg_color=None  # 或者设置成 (0,0,0) 黑色背景
    ).with_duration(duration)

    return final_clip



# def move(clip:VideoClip, duration=2, intensity=100, direction='up', easing=ease_in_out_quad):
#     def pos_func(t):
#         y_offset = intensity * easing(t / duration)
#         if direction == 'up':
#             return ('center', 'center') if y_offset > clip.h/2 else ('center', -y_offset)
#         elif direction == 'down':
#             return ('center', 'center') if y_offset > clip.h/2 else ('center', clip.h - y_offset)
#         else:
#             return ('center', 'center')
#     scaled_clip = clip.resized(1.5)  # 根据实际情况调整放大比例
#     return scaled_clip.with_position(pos_func).with_duration(duration)

def calculate_scale_for_rotation(angle_degrees, width, height):
    """
    计算为避免旋转时露出黑边所需的最小放大比例。
    """
    angle_rad = math.radians(angle_degrees % 360)
    # 获取原始宽高比
    original_ratio = float(width) / height
    
    # 根据旋转角度调整宽高比
    if angle_degrees % 180 == 90:
        new_ratio = 1.0 / original_ratio
    else:
        new_ratio = original_ratio

    # 计算新的宽度和高度，以确保旋转后不会出现黑边
    diagonal = math.sqrt(width ** 2 + height ** 2)
    scale_factor = diagonal / min(width, height)

    return scale_factor

def rotate(clip: VideoClip, duration=2, degrees=360, easing=ease_in_out_quad):
    """
    创建一个平滑旋转的视频效果，并通过预放大防止旋转时露出黑边。
    
    参数:
        clip (VideoClip): 输入视频剪辑。
        duration (float): 动画持续时间（秒）。
        degrees (float): 总共旋转的角度（如 90, 180, 360）。
        easing (function): 插值函数，输入 [0,1] 输出 [0,1]
        
    返回:
        VideoClip: 旋转动画视频。
    """
    w, h = clip.size
    original_size = (w, h)

    # 计算旋转所需最小放大倍数
    scale_factor = calculate_scale_for_rotation(degrees, w, h)
    
    # 预放大图像以防止旋转时露出黑边
    pre_scaled_clip = clip.with_effects([vfx.Resize(scale_factor)])

    # 定义动态旋转函数
    def rotation_func(t):
        if t >= duration:
            return degrees
        progress = easing(t / duration)
        return degrees * progress

    # 创建旋转动画剪辑
    animated_clip = (
        pre_scaled_clip
        .rotated(lambda t: rotation_func(t))  # 使用自定义旋转函数
        .with_position(("center", "center"))   # 确保居中旋转
        .with_duration(duration)
    )

    # 将旋转后的剪辑放入固定尺寸的合成剪辑中，防止画面变形
    final_clip = CompositeVideoClip(
        [animated_clip],
        size=original_size,
        bg_color=None  # 可选黑色背景或者透明背景
    ).with_duration(duration)

    return final_clip




# def follow(clip:VideoClip, duration=2, path_function=lambda t: (100 * t, 100 * t), easing=ease_in_out_quad):
#     def pos_func(t):
#         x, y = path_function(easing(t / duration))
#         return (x, y)
#     # 对于复杂路径可能需要预先放大图像
#     scaled_clip = clip.resized(1.5)  # 根据实际情况调整放大比例
#     return scaled_clip.with_position(pos_func).with_duration(duration)


def fisheye_distortion(image, strength=0.5):
    """Apply fisheye effect to an image."""
    height, width = image.shape[:2]
    map_x = np.zeros((height, width), dtype=np.float32)
    map_y = np.zeros((height, width), dtype=np.float32)

    center_x, center_y = width // 2, height // 2
    radius = min(center_x, center_y)

    for y in range(height):
        for x in range(width):
            dx = x - center_x
            dy = y - center_y
            distance = np.sqrt(dx**2 + dy**2)
            angle = np.arctan2(dy, dx)
            
            # Apply fish-eye transformation.
            factor = 1.0 + (strength * distance / radius)
            new_distance = distance * factor
            
            new_x = int(round(new_distance * np.cos(angle))) + center_x
            new_y = int(round(new_distance * np.sin(angle))) + center_y
            
            if 0 <= new_x < width and 0 <= new_y < height:
                map_x[y, x] = new_x
                map_y[y, x] = new_y
            else:
                map_x[y, x] = x
                map_y[y, x] = y
    
    fisheye_image = cv2.remap(image, map_x, map_y, interpolation=cv2.INTER_LINEAR)
    return fisheye_image

def apply_fisheye_and_pan(clip: VideoClip, duration=2, intensity=100, direction='left', easing=ease_in_out_quad):
    """
    对视频剪辑先应用鱼眼然后再应用移动，来模拟摄像机的绕z轴旋转拍摄。
    
    参数:
        clip (VideoClip): 要处理的视频剪辑。
        duration (int/float): 时长。
        intensity (int/float): 平移强度，单位为像素。
        direction (str): 平移方向，支持 'left', 'right'。
        
    返回:
        VideoClip: 模拟摄像机的绕z轴旋转的新视频剪辑。
    """
    w, h = clip.size
    original_size = (w, h)

    def make_frame(t):
        frame = clip.get_frame(t)
        frame = fisheye_distortion(frame)  # 应用鱼眼效果
        
        # 计算平移距离
        progress = easing(t / duration)
        offset = intensity * progress
        
        if direction == 'left':
            x_offset = -offset
        elif direction == 'right':
            x_offset = offset
        else:
            x_offset = 0

        # 确保 x_offset 是整数
        x_offset_int = int(round(x_offset))

        # 创建空白背景，防止黑边
        background = np.zeros((h, w * 2, 3), dtype=np.uint8)  # 宽度放大一倍以容纳平移

        # 计算源和目标区域
        src_start = max(0, -x_offset_int)
        src_end = min(w, w - x_offset_int)
        dst_start = max(0, x_offset_int)
        dst_end = dst_start + (src_end - src_start)

        # 只有在范围内才复制图像
        if src_start < src_end and dst_start < background.shape[1]:
            background[:, dst_start:dst_end, :] = frame[:, src_start:src_end, :]

        # 裁剪回原始大小
        final_frame = background[:, w//2:w//2 + w, :]

        return final_frame

    animated_clip = VideoClip(make_frame, duration=duration)
    final_clip = CompositeVideoClip([animated_clip], size=original_size).with_duration(duration)
    
    return final_clip




def blur(clip, sigma=3):
    """
    对视频剪辑中的每一帧应用高斯模糊。
    
    参数:
        clip (VideoClip): 要处理的视频剪辑。
        sigma (int/float): 高斯模糊的标准差，值越大越模糊。
        
    返回:
        VideoClip: 经过高斯模糊处理的新视频剪辑。
    """
    def blurred_frame(t):
        frame = clip.get_frame(t)
        # 使用OpenCV进行高斯模糊
        return cv2.GaussianBlur(frame, (0, 0), sigmaX=sigma)
    blurred_clip = VideoClip(
        frame_function=blurred_frame,
        duration=clip.duration,
    )

    return blurred_clip




def radial_blur(clip, center=None, max_sigma=10):
    """
    对视频剪辑中的每一帧应用径向模糊。
    模糊强度随距离中心点的距离而变化。
    
    参数:
        clip (VideoClip): 要处理的视频剪辑。
        center (tuple): 模糊中心点 (x, y)，默认为图像中心。
        max_sigma (int/float): 最大模糊强度（标准差）。
        
    返回:
        VideoClip: 应用了径向模糊的新视频剪辑。
    """
    def blurred_frame(t):
        frame = clip.get_frame(t)
        h, w, _ = frame.shape

        # 默认使用画面中心
        if center is None:
            cx, cy = w // 2, h // 2
        else:
            cx, cy = center

        # 创建网格坐标
        x = np.arange(w)
        y = np.arange(h)
        X, Y = np.meshgrid(x, y)
        
        # 计算每个像素到中心的距离
        dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
        dist_normalized = dist / np.max(dist)
        
        # 每个像素的模糊程度取决于其与中心的距离
        sigma_map = max_sigma * dist_normalized

        # 分通道处理（因为OpenCV的GaussianBlur不支持逐像素sigma）
        blurred_channels = []
        for i in range(3):
            # blurred_channel = gaussian_filter(frame[:, :, i], sigma=sigma_map)
            # blurred_channels.append(blurred_channel)
            channel = frame[:, :, i].copy()
            # 使用 OpenCV 的高斯模糊，模拟局部模糊（虽然不是严格的逐像素不同）
            # 这里我们使用最大 sigma 做一次模糊，然后根据 sigma_map 缩放模糊结果
            # 或者你可以做多尺度模糊合成
            blurred_full = cv2.GaussianBlur(channel, (0, 0), max_sigma)
            # 简单加权混合原图和模糊图（可替换为更复杂方式）
            alpha = sigma_map / max_sigma
            blurred_channel = (channel * (1 - alpha) + blurred_full * alpha).astype(np.uint8)
            blurred_channels.append(blurred_channel)
        
        blurred = np.stack(blurred_channels, axis=-1).astype(np.uint8)
        return blurred

    return VideoClip(
        frame_function=blurred_frame,
        duration=clip.duration,
        is_mask=clip.is_mask
    )




def directional_blur(
    clip: VideoClip,
    angle: float = 0.0,     # 模糊方向（角度），0 表示水平向右
    blur_len: int = 15      # 模糊长度（像素数）
) -> VideoClip:
    """
    对视频帧应用方向模糊，模拟运动轨迹效果。
    
    参数:
        clip (VideoClip): 原始视频剪辑。
        angle (float): 模糊方向，单位为度（0~360）。
        blur_len (int): 模糊长度，值越大越模糊。
        
    返回:
        VideoClip: 应用了方向模糊的新视频剪辑。
    """
    def make_frame(t):
        frame = clip.get_frame(t)

        # 创建一个线性运动模糊的核（kernel）
        kernel_size = blur_len
        kernel = np.zeros((kernel_size, kernel_size), dtype=np.float32)
        center = (kernel_size - 1) // 2

        # 计算模糊方向的角度对应的正余弦
        rad = np.deg2rad(angle)
        x = np.cos(rad)
        y = np.sin(rad)

        # 在 kernel 上绘制一条线（模拟运动轨迹）
        for i in range(kernel_size):
            px = int(np.round(x * i)) + center
            py = int(np.round(y * i)) + center
            if 0 <= px < kernel_size and 0 <= py < kernel_size:
                kernel[py, px] = 1

        kernel = kernel / kernel.sum()  # 归一化

        # 对每个通道应用卷积模糊
        blurred = cv2.filter2D(frame, -1, kernel)

        return blurred

    return VideoClip(make_frame, duration=clip.duration)



def pixelate(clip: VideoClip, block_size=10) -> VideoClip:
    """
    将画面像素化，模拟马赛克效果。
    
    参数:
        clip (VideoClip): 原始视频剪辑。
        block_size (int): 每个像素块的大小。
        
    返回:
        VideoClip: 像素化后的视频。
    """
    def make_frame(t):
        frame = clip.get_frame(t)  # frame 是 numpy.ndarray，shape=(h, w, 3)
        img = Image.fromarray(frame)
        w, h = img.size  # PIL 使用 .size 获取宽高
        
        # 缩小再放大实现马赛克效果
        small = img.resize((w // block_size, h // block_size), Image.NEAREST)
        mosaic = small.resize((w, h), Image.NEAREST)
        
        # 转换回 numpy array
        return np.array(mosaic)  # ✅ 关键：转为 ndarray

    return VideoClip(make_frame, duration=clip.duration)




def edge_detect(clip: VideoClip) -> VideoClip:
    """
    对视频帧应用边缘检测滤镜（灰度图像）。效果挺震撼。类似雕版印刷
    
    参数:
        clip (VideoClip): 原始视频剪辑。
        
    返回:
        VideoClip: 边缘检测后的视频。
    """
    def make_frame(t):
        frame = clip.get_frame(t)
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, threshold1=50, threshold2=150)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

    return VideoClip(make_frame, duration=clip.duration)



def posterize(clip: VideoClip, levels=4) -> VideoClip:
    """
    减少颜色层次，使画面具有“海报”风格。
    
    参数:
        clip (VideoClip): 原始视频剪辑。
        levels (int): 颜色层级数。
        
    返回:
        VideoClip: 海报风格视频。
    """
    def make_frame(t):
        frame = clip.get_frame(t)
        return np.floor(frame / 256 * levels) * (256 // levels)

    return VideoClip(make_frame, duration=clip.duration)


def shake(clip: VideoClip, intensity=5) -> VideoClip:
    """
    让画面随机轻微抖动，模拟手持拍摄效果。
    
    参数:
        clip (VideoClip): 原始视频剪辑。
        intensity (int): 抖动最大偏移量。
        
    返回:
        VideoClip: 抖动效果的视频。
    """
    def make_frame(t):
        frame = clip.get_frame(t)
        dx = random.randint(-intensity, intensity)
        dy = random.randint(-intensity, intensity)
        return np.roll(frame, shift=(dy, dx), axis=(0, 1))

    return VideoClip(make_frame, duration=clip.duration)



def glitch(clip: VideoClip, intensity=3) -> VideoClip:
    """
    简单模拟横向错位的数码故障效果。类似画面抖动
    
    参数:
        clip (VideoClip): 原始视频。
        intensity (int): 错位强度。
        
    返回:
        VideoClip: 故障风视频。
    """
    def make_frame(t):
        frame = clip.get_frame(t)
        h, w, d = frame.shape
        offset = random.randint(-intensity, intensity)
        new_frame = frame.copy()
        if offset > 0:
            new_frame[:, :w - offset] = frame[:, offset:]
        elif offset < 0:
            new_frame[:, -offset:] = frame[:, :w + offset]
        return new_frame

    return VideoClip(make_frame, duration=clip.duration)


def vignette(clip: VideoClip, strength=0.5) -> VideoClip:
    """
    添加暗角效果，突出画面中心。
    
    参数:
        clip (VideoClip): 原始视频。
        strength (float): 暗角强度 [0~1]。
        
    返回:
        VideoClip: 添加暗角的视频。
    """
    def make_frame(t):
        frame = clip.get_frame(t)
        h, w, _ = frame.shape
        x = np.linspace(-1, 1, w)
        y = np.linspace(-1, 1, h)
        X, Y = np.meshgrid(x, y)
        dist = 1 - (X ** 2 + Y ** 2)
        mask = np.clip(dist, 0, 1)
        mask = 1 - strength * (1 - mask)
        return (frame * mask[..., np.newaxis]).astype(np.uint8)

    return VideoClip(make_frame, duration=clip.duration)

# 创建带黑色半透明遮罩的复合视频
def apply_black_overlay(clip, opacity=50):
    """
    在视频上叠加一个黑色半透明遮罩。
    
    参数:
        clip: 原始视频剪辑。
        opacity: 透明度 (0 完全透明, 100完全不透明)
        
    返回:
        新的合成视频剪辑
    """
    opacity=int(opacity/100*255)
    overlay = ColorClip(size=clip.size, color=(0, 0, 0,opacity), duration=clip.duration)
    # overlay = overlay.set_opacity(opacity)  # 设置透明度
    return CompositeVideoClip([clip, overlay])




def wave_frame(img, t):
    """
    对单帧图像应用水波抖动效果
    :param img: numpy array 格式的图像 (H, W, C)
    :param t: 当前时间
    :return: 处理后的图像
    """
    height, width = img.shape[:2]

    # 创建一个与原图大小相同的空白图像
    distorted = np.zeros_like(img)

    # 创建网格坐标
    x, y = np.meshgrid(np.arange(width), np.arange(height))

    # 添加正弦扰动
    dx = 5 * np.sin(2 * np.pi * t + y / 20)  # 水平方向波动
    dy = 3 * np.cos(2 * np.pi * t + x / 20)  # 垂直方向波动

    map_x = (x + dx).astype(np.float32)
    map_y = (y + dy).astype(np.float32)

    # 应用重映射（remap）
    distorted = cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_REFLECT)

    return distorted

def make_wavy_image_func(clip):
    def func(get_frame, t):
        frame = get_frame(t)
        return wave_frame(frame, t)
    return func

# 使用示例
if __name__ == '__main__':


    # # 图片路径
    # image_path = "7A9D4C44D6474DE877C49012B777D11A.jpg"
    # clip=ImageClip(image_path)

    # # 创建多个镜头效果片段
    # zoom = zoom_in(clip, duration=2, intensity=0.5)
    # pan_left = pan(clip, duration=2, intensity=150, direction='left')
    # # swing_clip = swing(clip, duration=2, amplitude=80, frequency=1.5)
    # rotate_clip = rotate(clip, duration=2, degrees=360)
    # follow_curve = follow(
    #     clip,
    #     duration=2,
    #     path_function=lambda t: (200 * t, 100 * np.sin(np.pi * t)),  # 贝塞尔曲线
    # )

    # # 合成到一个视频中
    # final_video = concatenate_videoclips([zoom, pan_left,  rotate_clip, follow_curve],method='compose')

    # # 导出视频
    # final_video.write_videofile("dynamic_effects.mp4", fps=24,codec="libx264")
    video = VideoFileClip("cliptest/video3.mp4")

    # 径向模糊，中心在 (320, 240)，最大模糊强度为10
    radial_blurred_video = rotate(video)
    radial_blurred_video.write_videofile("cliptest/t1/radial_blur_output.mp4",fps=24, codec="libx264")