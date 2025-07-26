from moviepy import CompositeVideoClip, ImageSequenceClip, vfx,ImageClip,concatenate_videoclips,ColorClip,VideoClip,VideoFileClip
import numpy as np
import cv2
# from core.clipeffects.easy_clip_effects import directional_blur



def directional_blur(
    clip: VideoClip,
    angle: float = 0.0,     # 模糊方向（角度），0 表示水平向右
    blur_len: int = 15      # 模糊长度（像素数）
) -> VideoClip:
    """
    对视频帧应用方向模糊，模拟运动轨迹效果。别引用，这个是用来满足径向模糊转场的
    
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


# 创建一个简单的黑色渐隐转场
def black_transition(clipA: VideoClip, clipB: VideoClip=None, duration=0.5, position="center"):
    """
    在 clipA 和 clipB 之间添加黑色渐隐转场
    
    参数:
        clipA (VideoClip): 第一个视频
        clipB (VideoClip): 第二个视频
        duration (float): 转场持续时间
        position (str): "start", "center", "end"
        
    返回:
        VideoFileClip: 合成后的视频
    """
    if clipB is None:
        final_clip = clipA.with_effects([vfx.FadeOut(duration)])
        return final_clip
    # 获取视频分辨率
    size = clipA.size if clipA else clipB.size

    # 创建一个纯黑背景的遮罩 clip
    black_clip = ColorClip(size=size, color=(0, 0, 0), duration=duration)

    # 设置 clipA 的淡出
    if position in ["end"]:
        clipA = clipA.with_effects([vfx.FadeOut(duration)])
    if position in ["center"]:
        clipA = clipA.with_effects([vfx.FadeOut(duration / 2)])
         # 设置 clipB 的淡出
        clipB = clipB.with_effects([vfx.FadeIn(duration/2)])
    # 设置 clipB 的淡入
    if position in ["start"]:
        clipB = clipB.with_effects([vfx.FadeIn(duration)])

    # clipA 放在前面，然后插入 black_clip 作为过渡（也可以省略）
    total_duration = clipA.duration + duration + clipB.duration
    final_clip = CompositeVideoClip([
        clipA.with_start(0),
        black_clip.with_start(clipA.duration),  # 可选
        clipB.with_start(clipA.duration + duration)
    ], size=size)

    return final_clip.with_duration(total_duration)

# def img_transition(img_path:str,clipA: VideoFileClip, clipB: VideoFileClip=None, duration=0.5, position="center"):
#     '''图片转场'''
#     transition_image = ImageClip(img_path).with_duration(duration)
#     return transition_image


def crossfade_transition(clipA: VideoClip, clipB: VideoClip = None, duration=0.5):
    """
    创建一个交叉渐隐转场效果，用于两个视频之间的平滑过渡。
    
    参数:
        clipA (VideoClip): 第一个视频片段（可以为 None）
        clipB (VideoClip): 第二个视频片段（可以为 None）
        duration (float): 转场持续时间（秒）
        position (str): "start", "center", "end"，控制转场发生位置
        
    返回:
        VideoFileClip: 合成后的视频剪辑
    """
    finalclip=CompositeVideoClip([
                              clipA.subclipped(clipA.duration-duration),
                              clipB.subclipped(0,duration).with_effects([vfx.CrossFadeIn(duration)])])
    finalclip=concatenate_videoclips([clipA.subclipped(0,clipA.duration-duration),finalclip, clipB.subclipped(duration,clipB.duration)], method="compose")
    return finalclip
    # if clipA is None and clipB is None:
    #     raise ValueError("clipA 和 clipB 不能都为 None")

    # # 获取视频尺寸（默认使用非空 clip 的尺寸）
    # size = clipA.size if clipA else clipB.size

    # clips = []

    # # 处理 clipA（如果有）
    # if clipA:
    #     if position in ["center", "end"]:
    #         clipA = clipA.subclipped(0, clipA.duration - duration).with_effects([vfx.CrossFadeOut(duration)])
    #     clips.append(clipA.with_start(0))

    # # 处理 clipB（如果有）
    # if clipB:
    #     if position in ["center", "start"]:
    #         clipB = clipB.subclipped(duration).with_effects([vfx.CrossFadeIn(duration)])
    #     start_time = clipA.duration if clipA else 0
    #     clips.append(clipB.with_start(start_time))

    

    # # 计算总时长
    # total_duration = 0
    # if clipA:
    #     total_duration += clipA.duration
    # if clipB:
    #     if position == "center":
    #         total_duration += clipB.duration
    #     elif position == "start":
    #         total_duration += clipB.duration + duration
    #     elif position == "end":
    #         total_duration += duration + clipB.duration

    # # 合成视频
    # return CompositeVideoClip(clips, size=size).with_duration(total_duration)


def circular_crossfadein_transition(clipA: VideoClip, clipB: VideoClip = None, duration=0.5):
    """
    创建一个圆形渐隐交叉转场，clipB 从圆形扩散中显现。
    
    参数:
        clipA (VideoClip): 第一个视频片段（可为 None）
        clipB (VideoClip): 第二个视频片段（可为 None）
        duration (float): 转场持续时间
        
    返回:
        CompositeVideoClip: 合成后的视频片段
    """
    if clipA is None and clipB is None:
        raise ValueError("clipA 和 clipB 不能都为 None")

    size = clipA.size if clipA else clipB.size
    center = (size[0] // 2, size[1] // 2)
    max_radius = np.hypot(size[0], size[1])  # 最大半径（对角线）

    clips = []

    # 处理 clipA（如果有）
    if clipA:
        def make_frame_A(t):
            frame = clipA.get_frame(t)
            if t > clipA.duration - duration:
                progress = max(0.0, (clipA.duration - t) / duration)
                radius = progress * max_radius
                y, x = np.ogrid[:size[1], :size[0]]
                dist = np.sqrt((x - center[0])**2 + (y - center[1])**2)
                mask = (dist <= radius).astype(np.float64)
                return (frame * mask[..., np.newaxis]).astype(np.uint8)
            else:
                return frame

        faded_clipA = VideoClip(make_frame_A, duration=clipA.duration).with_fps(clipA.fps)
        clips.append(faded_clipA.with_start(0))

    # 处理 clipB（如果有）
    if clipB:
        start_time = clipA.duration if clipA else 0

        def make_frame_B(t):
            raw_t = t + start_time
            frame = clipB.get_frame(t)
            if raw_t < start_time + duration:
                progress = raw_t / duration
                radius = progress * max_radius
                y, x = np.ogrid[:size[1], :size[0]]
                dist = np.sqrt((x - center[0])**2 + (y - center[1])**2)
                mask = (dist <= radius).astype(np.float64)
                return (frame * mask[..., np.newaxis]).astype(np.uint8)
            else:
                return frame

        faded_clipB = VideoClip(make_frame_B, duration=clipB.duration).with_fps(clipB.fps)
        clips.append(faded_clipB.with_start(start_time))

    total_duration = 0
    if clipA:
        total_duration += clipA.duration
    if clipB:
        if clipA:
            total_duration = max(clipA.duration, start_time + clipB.duration)
        else:
            total_duration += clipB.duration

    return CompositeVideoClip(clips, size=size).with_duration(total_duration)

##TODO: 百叶窗转场,现在百叶窗出不来

def blinds_transition(clipA: VideoClip, clipB: VideoClip = None, duration=0.5, num_blinds=5, direction="vertical"):
    """
    创建一个百叶窗转场效果
    
    参数:
        clipA (VideoClip): 第一个视频片段（可为 None）
        clipB (VideoClip): 第二个视频片段（可为 None）
        duration (float): 转场持续时间
        num_blinds (int): 百叶窗的数量
        direction (str): "vertical" 或 "horizontal"
        
    返回:
        CompositeVideoClip: 合成后的视频片段
    """
    if clipA is None and clipB is None:
        raise ValueError("clipA 和 clipB 不能都为 None")

    size = clipA.size if clipA else clipB.size
    clips = []

    # 处理 clipA（如果有）
    if clipA:
        def make_frame_A(t):
            frame = clipA.get_frame(t)
            if t > clipA.duration - duration:
                progress = max(0.0, (clipA.duration - t) / duration)
                active_blinds = int(progress * num_blinds)

                mask = np.zeros((size[1], size[0]), dtype=np.float64)

                if direction == "vertical":
                    blind_width = size[0] // num_blinds
                    for i in range(num_blinds - active_blinds, num_blinds):
                        start_x = i * blind_width
                        end_x = start_x + blind_width
                        mask[:, start_x:end_x] = 1.0
                elif direction == "horizontal":
                    blind_height = size[1] // num_blinds
                    for i in range(num_blinds - active_blinds, num_blinds):
                        start_y = i * blind_height
                        end_y = start_y + blind_height
                        mask[start_y:end_y, :] = 1.0

                return (frame * mask[..., np.newaxis]).astype(np.uint8)
            else:
                return frame

        faded_clipA = VideoClip(make_frame_A, duration=clipA.duration).with_fps(clipA.fps)
        clips.append(faded_clipA.with_start(0))

    # 处理 clipB（如果有）
    if clipB:
        start_time = clipA.duration if clipA else 0

        def make_frame_B(t):
            raw_t = t + start_time
            frame = clipB.get_frame(t)
            if raw_t < start_time + duration:
                progress = raw_t / duration
                active_blinds = int(progress * num_blinds)

                mask = np.zeros((size[1], size[0]), dtype=np.float64)

                if direction == "vertical":
                    blind_width = size[0] // num_blinds
                    for i in range(active_blinds):
                        start_x = i * blind_width
                        end_x = start_x + blind_width
                        mask[:, start_x:end_x] = 1.0
                elif direction == "horizontal":
                    blind_height = size[1] // num_blinds
                    for i in range(active_blinds):
                        start_y = i * blind_height
                        end_y = start_y + blind_height
                        mask[start_y:end_y, :] = 1.0

                return (frame * mask[..., np.newaxis]).astype(np.uint8)
            else:
                return frame

        faded_clipB = VideoClip(make_frame_B, duration=clipB.duration).with_fps(clipB.fps)
        clips.append(faded_clipB.with_start(start_time))

    total_duration = 0
    if clipA:
        total_duration += clipA.duration
    if clipB:
        if clipA:
            total_duration = max(clipA.duration, start_time + clipB.duration)
        else:
            total_duration += clipB.duration

    return CompositeVideoClip(clips, size=size).with_duration(total_duration)




def slide_transition(clipA: VideoClip, clipB: VideoClip = None, duration=0.5, direction="left"):
    """
    创建一个滑动转场的效果
    
    参数:
        clipA (VideoClip): 第一个视频片段（可为 None）
        clipB (VideoClip): 第二个视频片段（可为 None）
        duration (float): 转场持续时间
        direction (str): "left" 或 "right"或 "top" 或 "bottom"，控制滑动方向
        
    返回:
        CompositeVideoClip: 合成后的视频片段
    """

    if clipA is None and clipB is None:
        raise ValueError("clipA 和 clipB 不能都为 None")

    size = clipA.size if clipA else clipB.size
    clips = []

    # 处理 clipA（如果有）
    if clipA:
        def make_frame_A(t):
            frame = clipA.get_frame(t)
            if t > clipA.duration - duration:
                progress = max(0.0, (clipA.duration - t) / duration)

                h, w = size[1], size[0]
                new_frame = np.zeros_like(frame)

                if direction == "left":
                    offset = int((1 - progress) * w)
                    new_frame[:, :w - offset] = frame[:, offset:]
                elif direction == "right":
                    offset = int(progress * w)
                    new_frame[:, offset:] = frame[:, :w - offset]
                elif direction == "top":
                    offset = int((1 - progress) * h)
                    new_frame[:h - offset, :] = frame[offset:, :]
                elif direction == "bottom":
                    offset = int(progress * h)
                    new_frame[offset:, :] = frame[:h - offset, :]

                return new_frame
            else:
                return frame

        faded_clipA = VideoClip(make_frame_A, duration=clipA.duration).with_fps(clipA.fps)
        clips.append(faded_clipA.with_start(0))

    # 处理 clipB（如果有）
    if clipB:
        start_time = clipA.duration if clipA else 0

        def make_frame_B(t):
            raw_t = t + start_time
            frame = clipB.get_frame(t)
            if raw_t < start_time + duration:
                progress = raw_t / duration

                h, w = size[1], size[0]
                new_frame = np.zeros_like(frame)

                if direction == "left":
                    offset = int((1 - progress) * w)
                    new_frame[:, offset:] = frame[:, :w - offset]
                elif direction == "right":
                    offset = int(progress * w)
                    new_frame[:, :w - offset] = frame[:, offset:]
                elif direction == "top":
                    offset = int((1 - progress) * h)
                    new_frame[offset:, :] = frame[:h - offset, :]
                elif direction == "bottom":
                    offset = int(progress * h)
                    new_frame[:h - offset, :] = frame[offset:, :]

                return new_frame
            else:
                return frame

        faded_clipB = VideoClip(make_frame_B, duration=clipB.duration).with_fps(clipB.fps)
        clips.append(faded_clipB.with_start(start_time))

    total_duration = 0
    if clipA:
        total_duration += clipA.duration
    if clipB:
        if clipA:
            total_duration = max(clipA.duration, start_time + clipB.duration)
        else:
            total_duration += clipB.duration

    return CompositeVideoClip(clips, size=size).with_duration(total_duration)


def zoom_transition(clipA: VideoClip, clipB: VideoClip = None, duration=0.5):
    """
    创建一个缩放转场的效果
    
    参数:
        clipA (VideoClip): 第一个视频片段（可为 None）
        clipB (VideoClip): 第二个视频片段（可为 None）
        duration (float): 转场持续时间
        
    返回:
        CompositeVideoClip: 合成后的视频片段
    """

    if clipA is None and clipB is None:
        raise ValueError("clipA 和 clipB 不能都为 None")

    size = clipA.size if clipA else clipB.size
    center = (size[0] // 2, size[1] // 2)
    clips = []

    # 处理 clipA（如果有）
    if clipA:
        def make_frame_A(t):
            frame = clipA.get_frame(t)
            if t > clipA.duration - duration:
                progress = max(0.0, (clipA.duration - t) / duration)
                scale = 1.0 + (1.0 - progress) * 0.5  # 最大放大 1.5 倍

                from scipy.ndimage import zoom
                scaled = zoom(frame, (scale, scale, 1), order=1)

                # 居中裁剪
                y_start = (scaled.shape[0] - size[1]) // 2
                x_start = (scaled.shape[1] - size[0]) // 2
                cropped = scaled[y_start:y_start+size[1], x_start:x_start+size[0]]
                return cropped.astype(np.uint8)
            else:
                return frame

        faded_clipA = VideoClip(make_frame_A, duration=clipA.duration).with_fps(clipA.fps)
        clips.append(faded_clipA.with_start(0))

    # 处理 clipB（如果有）
    if clipB:
        start_time = clipA.duration if clipA else 0

        def make_frame_B(t):
            raw_t = t + start_time
            frame = clipB.get_frame(t)
            if raw_t < start_time + duration:
                progress = raw_t / duration
                scale = 1.0 + progress * 0.5

                from scipy.ndimage import zoom
                scaled = zoom(frame, (scale, scale, 1), order=1)

                y_start = (scaled.shape[0] - size[1]) // 2
                x_start = (scaled.shape[1] - size[0]) // 2
                cropped = scaled[y_start:y_start+size[1], x_start:x_start+size[0]]
                return cropped.astype(np.uint8)
            else:
                return frame

        faded_clipB = VideoClip(make_frame_B, duration=clipB.duration).with_fps(clipB.fps)
        clips.append(faded_clipB.with_start(start_time))

    total_duration = 0
    if clipA:
        total_duration += clipA.duration
    if clipB:
        if clipA:
            total_duration = max(clipA.duration, start_time + clipB.duration)
        else:
            total_duration += clipB.duration

    return CompositeVideoClip(clips, size=size).with_duration(total_duration)




def rectangular_shrink_transition(clipA: VideoFileClip, clipB: VideoFileClip = None, duration=0.5):

    """
    创建一个矩形收缩转场的效果
    
    参数:
        clipA (VideoFClip): 第一个视频片段（可为 None）
        clipB (VideoClip): 第二个视频片段（可为 None）
        duration (float): 转场持续时间
        
    返回:
        CompositeVideoClip: 合成后的视频片段
    """
    if clipA is None and clipB is None:
        raise ValueError("clipA 和 clipB 不能都为 None")

    size = clipA.size if clipA else clipB.size
    center = (size[0] // 2, size[1] // 2)
    clips = []

    # 处理 clipA（如果有）
    if clipA:
        def make_frame_A(t):
            frame = clipA.get_frame(t)
            if t > clipA.duration - duration:
                progress = max(0.0, (clipA.duration - t) / duration)
                w_ratio = int(progress * size[0])
                h_ratio = int(progress * size[1])

                x1 = w_ratio // 2
                y1 = h_ratio // 2
                x2 = size[0] - w_ratio // 2
                y2 = size[1] - h_ratio // 2

                new_frame = np.zeros_like(frame)
                new_frame[y1:y2, x1:x2] = frame[y1:y2, x1:x2]
                return new_frame
            else:
                return frame

        faded_clipA = VideoClip(make_frame_A, duration=clipA.duration).with_fps(clipA.fps)
        clips.append(faded_clipA.with_start(0))

    # 处理 clipB（如果有）
    if clipB:
        start_time = clipA.duration if clipA else 0

        def make_frame_B(t):
            raw_t = t + start_time
            frame = clipB.get_frame(t)
            if raw_t < start_time + duration:
                progress = raw_t / duration
                w_ratio = int((1 - progress) * size[0])
                h_ratio = int((1 - progress) * size[1])

                x1 = w_ratio // 2
                y1 = h_ratio // 2
                x2 = size[0] - w_ratio // 2
                y2 = size[1] - h_ratio // 2

                new_frame = np.zeros_like(frame)
                new_frame[y1:y2, x1:x2] = frame[y1:y2, x1:x2]
                return new_frame
            else:
                return frame

        faded_clipB = VideoClip(make_frame_B, duration=clipB.duration).with_fps(clipB.fps)
        clips.append(faded_clipB.with_start(start_time))

    total_duration = 0
    if clipA:
        total_duration += clipA.duration
    if clipB:
        if clipA:
            total_duration = max(clipA.duration, start_time + clipB.duration)
        else:
            total_duration += clipB.duration

    return CompositeVideoClip(clips, size=size).with_duration(total_duration)




##TODO: 径向模糊转场,现在没有往径向的方向去移动进来，还有要增加径向参数
def directional_transition(clip1:VideoClip,clip2:VideoClip,duration=0.5):
    """
    创建一个径向模糊转场的效果
    
    参数:
        clip1 (VideoClip): 第一个视频片段（可为 None）
        clip2 (VideoClip): 第二个视频片段（可为 None）
        duration (float): 转场持续时间
        
    返回:
        CompositeVideoClip: 合成后的视频片段
    """

    # 定义转场持续时间
    transition_duration = duration

    # 对第一个剪辑的最后部分应用方向模糊
    blur_clip1 = clip1.subclipped(clip1.duration - transition_duration)
    blur_clip1=directional_blur(blur_clip1, 90, blur_len=20)

    # 对第二个剪辑的开始部分应用方向模糊
    blur_clip2 = clip2.subclipped(0, transition_duration)
    blur_clip2=directional_blur(blur_clip2, 90, blur_len=20)

    # 将模糊处理过的部分与原始剪辑拼接起来，并添加到主剪辑列表中
    clips = [
        clip1.subclipped(0, clip1.duration - transition_duration),
        crossfade_transition(blur_clip1, blur_clip2, transition_duration/2),
        clip2.subclipped(transition_duration)
    ]

    final_clip = concatenate_videoclips(clips, method="compose")
    return final_clip
    # final_clip.write_videofile("direction_blur_transition.mp4", codec='libx264')


##TODO: 旋转转场,现在转的不够有精神
def rotate_transition(clip1,clip2,duration=0.5):
    """
    创建一个旋转转场的效果
    
    参数:
        clip1 (VideoClip): 第一个视频片段（可为 None）
        clip2 (VideoClip): 第二个视频片段（可为 None）
        duration (float): 转场持续时间
        
    返回:
        CompositeVideoClip: 合成后的视频片段
    """

# 加载你的视频片段
    # clip1 = VideoFileClip("video1.mp4")
    # clip2 = VideoFileClip("video2.mp4")

    # 定义转场持续时间
    transition_duration = duration

    # 创建旋转效果
    rotated_end = clip1.subclipped(clip1.duration - transition_duration).with_effects([vfx.Rotate(lambda t: 360*t/transition_duration)])
    rotated_start = clip2.subclipped(0, transition_duration).with_effects([vfx.Rotate(lambda t: 360*(1-t/transition_duration))])

    # 组合剪辑和转场
    clips = [
        clip1.subclipped(0, clip1.duration - transition_duration),
        crossfade_transition(rotated_end, rotated_start, transition_duration/2),
        clip2.subclipped(transition_duration)
    ]

    final_clip = concatenate_videoclips(clips, method="compose")
    return final_clip

#
def flash_transition(clip1,clip2,duration=0.5):
    """
    创建一个闪白转场的效果
    
    参数:
        clip1 (VideoClip): 第一个视频片段（可为 None）
        clip2 (VideoClip): 第二个视频片段（可为 None）
        duration (float): 转场持续时间
        
    返回:
        CompositeVideoClip: 合成后的视频片段
    """

    # 定义转场持续时间
    transition_duration = duration

    # 创建白色flash剪辑
    flash = ColorClip(size=clip1.size, color=(255, 255, 255), duration=transition_duration)

    # 拼接所有剪辑
    final_clip = concatenate_videoclips([clip1, flash, clip2], method="compose")
    return final_clip


##TODO:划象转场，十字划象，更多划象

if __name__ == "__main__":
    # 示例用法
    clip1 = VideoFileClip("cliptest/video3.mp4")
    clip2 = VideoFileClip("cliptest/video4.mp4")

    result_clip = flash_transition(clip1,clip2,duration=0.5)
    result_clip.write_videofile("cliptest/t1/fade_transition.mp4", codec='libx264',fps=24)
    
    # # 使用交叉转场
    # result_clip = crossfade_transition(clip1, clip2, duration=0.5)
    # result_clip.write_videofile("crossfade_transition.mp4", codec='libx264')
    
    # # 使用方向转场
    # result_clip = directional_transition(clip1, clip2, duration=0.5)
    # result_clip.write_videofile("directional_transition.mp4", codec='libx264')
    
    # # 使用旋转转场
    # rotate_transition(duration=0.5)
    
    # # 使用闪光转场
    # flash_transition(duration=0.5)