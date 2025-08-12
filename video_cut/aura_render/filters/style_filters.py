"""
艺术风格滤镜实现
将8大艺术风格映射到具体的视频处理效果
"""

from moviepy import VideoClip, CompositeVideoClip, ColorClip
from moviepy.video.fx import FadeIn, FadeOut, Resize
import numpy as np
import cv2
from typing import Callable, Dict, Any


class StyleFilterEngine:
    """风格滤镜引擎"""
    
    def __init__(self):
        # 映射滤镜名称到实际处理函数
        self.filter_map = {
            # 复古赛博风格
            "neon_glow": self._neon_glow,
            "chromatic_aberration": self._chromatic_aberration,
            "scan_lines": self._scan_lines,
            "digital_noise": self._digital_noise,
            
            # 黑白默片风格
            "black_white": self._black_white,
            "film_grain": self._film_grain,
            "film_scratches": self._film_scratches,
            "flicker": self._flicker,
            
            # 梦幻仙境风格
            "soft_focus": self._soft_focus,
            "bloom": self._bloom,
            "fairy_dust": self._fairy_dust,
            "sparkles": self._sparkles,
            
            # 手绘动画风格
            "pencil_sketch": self._pencil_sketch,
            "watercolor": self._watercolor,
            "paper_texture": self._paper_texture,
            "brush_strokes": self._brush_strokes,
            
            # 极简扁平风格
            "posterize": self._posterize,
            "flat_color": self._flat_color,
            "clean_edges": self._clean_edges,
            "geometric_shapes": self._geometric_shapes,
            
            # 胶片质感风格
            "35mm_film": self._35mm_film,
            "halation": self._halation,
            "anamorphic_flare": self._anamorphic_flare,
            "film_burn": self._film_burn,
            
            # 故障艺术风格
            "datamosh": self._datamosh,
            "pixel_sort": self._pixel_sort,
            "rgb_shift": self._rgb_shift,
            "screen_tear": self._screen_tear,
            
            # 蒸汽波风格
            "vhs_effect": self._vhs_effect,
            "crt_screen": self._crt_screen,
            "pastel_gradient": self._pastel_gradient,
            "vhs_tracking": self._vhs_tracking,
            
            # 通用滤镜
            "vignette": self._vignette,
            "grain": self._grain,
            "blur": self._blur
        }
    
    def apply_filter(self, clip: VideoClip, filter_name: str, **params) -> VideoClip:
        """
        应用指定的滤镜到视频片段
        
        Args:
            clip: 视频片段
            filter_name: 滤镜名称
            **params: 滤镜参数
            
        Returns:
            处理后的视频片段
        """
        if filter_name in self.filter_map:
            return self.filter_map[filter_name](clip, **params)
        return clip
    
    # ============= 复古赛博风格滤镜 =============
    
    def _neon_glow(self, clip: VideoClip, intensity: float = 0.7) -> VideoClip:
        """霓虹发光效果"""
        def make_frame(t):
            frame = clip.get_frame(t)
            # 提取高亮区域
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            _, bright = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            
            # 创建发光效果
            glow = cv2.GaussianBlur(bright, (21, 21), 10)
            glow_colored = cv2.applyColorMap(glow, cv2.COLORMAP_HOT)
            glow_colored = cv2.cvtColor(glow_colored, cv2.COLOR_BGR2RGB)
            
            # 混合原图和发光
            result = cv2.addWeighted(frame, 1.0, glow_colored, intensity, 0)
            return np.clip(result, 0, 255).astype(np.uint8)
        
        return VideoClip(make_frame, duration=clip.duration)
    
    def _chromatic_aberration(self, clip: VideoClip, shift: int = 5) -> VideoClip:
        """色差效果"""
        def make_frame(t):
            frame = clip.get_frame(t)
            h, w = frame.shape[:2]
            result = np.zeros_like(frame)
            
            # 分离RGB通道并偏移
            result[:, shift:, 0] = frame[:, :-shift, 0]  # R通道右移
            result[:, :, 1] = frame[:, :, 1]  # G通道不变
            result[:, :-shift, 2] = frame[:, shift:, 2]  # B通道左移
            
            return result
        
        return VideoClip(make_frame, duration=clip.duration)
    
    def _scan_lines(self, clip: VideoClip, spacing: int = 3) -> VideoClip:
        """扫描线效果"""
        def make_frame(t):
            frame = clip.get_frame(t)
            h, w = frame.shape[:2]
            
            # 创建扫描线
            for y in range(0, h, spacing):
                frame[y:y+1, :] = frame[y:y+1, :] * 0.5
            
            return frame.astype(np.uint8)
        
        return VideoClip(make_frame, duration=clip.duration)
    
    def _digital_noise(self, clip: VideoClip, amount: float = 0.1) -> VideoClip:
        """数字噪声"""
        def make_frame(t):
            frame = clip.get_frame(t)
            noise = np.random.randint(0, 50, frame.shape, dtype=np.uint8)
            result = cv2.addWeighted(frame, 1 - amount, noise, amount, 0)
            return result
        
        return VideoClip(make_frame, duration=clip.duration)
    
    # ============= 黑白默片风格滤镜 =============
    
    def _black_white(self, clip: VideoClip, sepia: bool = False) -> VideoClip:
        """黑白/棕褐色效果"""
        def make_frame(t):
            frame = clip.get_frame(t)
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            
            if sepia:
                # 棕褐色调
                result = np.zeros_like(frame)
                result[:, :, 0] = np.clip(gray * 0.393 + gray * 0.769 + gray * 0.189, 0, 255)
                result[:, :, 1] = np.clip(gray * 0.349 + gray * 0.686 + gray * 0.168, 0, 255)
                result[:, :, 2] = np.clip(gray * 0.272 + gray * 0.534 + gray * 0.131, 0, 255)
            else:
                result = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
            
            return result.astype(np.uint8)
        
        return VideoClip(make_frame, duration=clip.duration)
    
    def _film_grain(self, clip: VideoClip, intensity: float = 0.3) -> VideoClip:
        """胶片颗粒"""
        def make_frame(t):
            frame = clip.get_frame(t)
            grain = np.random.normal(0, 25 * intensity, frame.shape)
            result = frame + grain
            return np.clip(result, 0, 255).astype(np.uint8)
        
        return VideoClip(make_frame, duration=clip.duration)
    
    def _film_scratches(self, clip: VideoClip, density: float = 0.1) -> VideoClip:
        """胶片划痕"""
        def make_frame(t):
            frame = clip.get_frame(t)
            h, w = frame.shape[:2]
            
            # 随机添加竖直划痕
            if np.random.random() < density:
                x = np.random.randint(0, w)
                frame[:, x:x+2] = 255
            
            return frame
        
        return VideoClip(make_frame, duration=clip.duration)
    
    def _flicker(self, clip: VideoClip, intensity: float = 0.2) -> VideoClip:
        """闪烁效果"""
        def make_frame(t):
            frame = clip.get_frame(t)
            flicker_amount = 1.0 + intensity * np.sin(t * 20)
            result = frame * flicker_amount
            return np.clip(result, 0, 255).astype(np.uint8)
        
        return VideoClip(make_frame, duration=clip.duration)
    
    # ============= 梦幻仙境风格滤镜 =============
    
    def _soft_focus(self, clip: VideoClip, strength: float = 0.5) -> VideoClip:
        """柔焦效果"""
        def make_frame(t):
            frame = clip.get_frame(t)
            blurred = cv2.GaussianBlur(frame, (15, 15), 5)
            result = cv2.addWeighted(frame, 1 - strength, blurred, strength, 0)
            return result
        
        return VideoClip(make_frame, duration=clip.duration)
    
    def _bloom(self, clip: VideoClip, threshold: int = 200) -> VideoClip:
        """泛光效果"""
        def make_frame(t):
            frame = clip.get_frame(t)
            # 提取高光部分
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            _, bright = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
            
            # 模糊高光创建光晕
            bloom = cv2.GaussianBlur(bright, (31, 31), 15)
            bloom_colored = cv2.merge([bloom, bloom, bloom])
            
            # 叠加到原图
            result = cv2.add(frame, bloom_colored // 2)
            return np.clip(result, 0, 255).astype(np.uint8)
        
        return VideoClip(make_frame, duration=clip.duration)
    
    def _fairy_dust(self, clip: VideoClip, particle_count: int = 50) -> VideoClip:
        """仙尘效果"""
        def make_frame(t):
            frame = clip.get_frame(t)
            h, w = frame.shape[:2]
            
            # 添加闪烁的粒子
            for _ in range(particle_count):
                if np.random.random() < 0.3:  # 30%概率显示
                    x = np.random.randint(0, w)
                    y = np.random.randint(0, h)
                    size = np.random.randint(1, 4)
                    cv2.circle(frame, (x, y), size, (255, 255, 200), -1)
            
            return frame
        
        return VideoClip(make_frame, duration=clip.duration)
    
    def _sparkles(self, clip: VideoClip) -> VideoClip:
        """闪光效果"""
        def make_frame(t):
            frame = clip.get_frame(t)
            h, w = frame.shape[:2]
            
            # 创建星星形状的闪光
            sparkle_mask = np.zeros((h, w), dtype=np.uint8)
            num_sparkles = int(10 * np.sin(t * 5) + 10)
            
            for _ in range(num_sparkles):
                x = np.random.randint(10, w - 10)
                y = np.random.randint(10, h - 10)
                cv2.drawMarker(sparkle_mask, (x, y), 255, cv2.MARKER_STAR, 10)
            
            sparkle_colored = cv2.merge([sparkle_mask, sparkle_mask, sparkle_mask * 0.8])
            result = cv2.add(frame, sparkle_colored.astype(np.uint8))
            
            return np.clip(result, 0, 255).astype(np.uint8)
        
        return VideoClip(make_frame, duration=clip.duration)
    
    # ============= 手绘动画风格滤镜 =============
    
    def _pencil_sketch(self, clip: VideoClip) -> VideoClip:
        """铅笔素描效果"""
        def make_frame(t):
            frame = clip.get_frame(t)
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            
            # 使用自适应阈值创建素描效果
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                         cv2.THRESH_BINARY, 7, 7)
            # 反转得到铅笔效果
            sketch = cv2.bitwise_not(edges)
            result = cv2.cvtColor(sketch, cv2.COLOR_GRAY2RGB)
            
            return result
        
        return VideoClip(make_frame, duration=clip.duration)
    
    def _watercolor(self, clip: VideoClip) -> VideoClip:
        """水彩画效果"""
        def make_frame(t):
            frame = clip.get_frame(t)
            
            # 使用双边滤波创建水彩效果
            smooth = cv2.bilateralFilter(frame, 15, 80, 80)
            
            # 使用边缘保留滤波增强效果
            result = cv2.edgePreservingFilter(smooth, flags=2, sigma_s=50, sigma_r=0.4)
            
            return result
        
        return VideoClip(make_frame, duration=clip.duration)
    
    def _paper_texture(self, clip: VideoClip) -> VideoClip:
        """纸张纹理"""
        def make_frame(t):
            frame = clip.get_frame(t)
            h, w = frame.shape[:2]
            
            # 创建纸张纹理
            texture = np.random.normal(220, 10, (h, w, 3))
            
            # 混合纹理和图像
            result = frame * 0.7 + texture * 0.3
            
            return np.clip(result, 0, 255).astype(np.uint8)
        
        return VideoClip(make_frame, duration=clip.duration)
    
    def _brush_strokes(self, clip: VideoClip) -> VideoClip:
        """笔触效果"""
        def make_frame(t):
            frame = clip.get_frame(t)
            
            # 使用形态学操作创建笔触
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            result = cv2.morphologyEx(frame, cv2.MORPH_GRADIENT, kernel)
            
            # 混合原图
            result = cv2.addWeighted(frame, 0.7, result, 0.3, 0)
            
            return result
        
        return VideoClip(make_frame, duration=clip.duration)
    
    # ============= 极简扁平风格滤镜 =============
    
    def _posterize(self, clip: VideoClip, levels: int = 4) -> VideoClip:
        """色调分离"""
        def make_frame(t):
            frame = clip.get_frame(t)
            # 减少颜色层次
            result = np.floor(frame / 256 * levels) * (256 // levels)
            return result.astype(np.uint8)
        
        return VideoClip(make_frame, duration=clip.duration)
    
    def _flat_color(self, clip: VideoClip) -> VideoClip:
        """扁平化颜色"""
        def make_frame(t):
            frame = clip.get_frame(t)
            
            # 使用K-means聚类减少颜色
            Z = frame.reshape((-1, 3))
            Z = np.float32(Z)
            
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            K = 8  # 颜色数量
            _, label, center = cv2.kmeans(Z, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            center = np.uint8(center)
            res = center[label.flatten()]
            result = res.reshape(frame.shape)
            
            return result
        
        return VideoClip(make_frame, duration=clip.duration)
    
    def _clean_edges(self, clip: VideoClip) -> VideoClip:
        """清晰边缘"""
        def make_frame(t):
            frame = clip.get_frame(t)
            
            # 边缘检测
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # 加粗边缘
            kernel = np.ones((2, 2), np.uint8)
            edges = cv2.dilate(edges, kernel, iterations=1)
            
            # 叠加边缘到原图
            edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
            result = cv2.subtract(frame, edges_colored // 4)
            
            return result
        
        return VideoClip(make_frame, duration=clip.duration)
    
    def _geometric_shapes(self, clip: VideoClip) -> VideoClip:
        """几何形状叠加"""
        def make_frame(t):
            frame = clip.get_frame(t)
            h, w = frame.shape[:2]
            
            # 随机添加几何形状
            overlay = frame.copy()
            if np.random.random() < 0.1:  # 10%概率
                shape_type = np.random.choice(['circle', 'rectangle', 'triangle'])
                color = tuple(np.random.randint(0, 255, 3).tolist())
                
                if shape_type == 'circle':
                    center = (np.random.randint(0, w), np.random.randint(0, h))
                    radius = np.random.randint(20, 100)
                    cv2.circle(overlay, center, radius, color, -1)
                elif shape_type == 'rectangle':
                    pt1 = (np.random.randint(0, w//2), np.random.randint(0, h//2))
                    pt2 = (np.random.randint(w//2, w), np.random.randint(h//2, h))
                    cv2.rectangle(overlay, pt1, pt2, color, -1)
            
            result = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
            return result
        
        return VideoClip(make_frame, duration=clip.duration)
    
    # ============= 故障艺术和其他滤镜实现略 =============
    # 由于篇幅限制，这里仅展示了部分滤镜的实现
    # 实际应用中需要完善所有滤镜的实现
    
    def _vignette(self, clip: VideoClip, strength: float = 0.5) -> VideoClip:
        """暗角效果"""
        def make_frame(t):
            frame = clip.get_frame(t)
            h, w = frame.shape[:2]
            
            # 创建径向渐变
            x = np.linspace(-1, 1, w)
            y = np.linspace(-1, 1, h)
            X, Y = np.meshgrid(x, y)
            dist = 1 - np.sqrt(X**2 + Y**2)
            dist = np.clip(dist, 0, 1)
            
            # 应用暗角
            vignette = 1 - strength * (1 - dist)
            result = frame * vignette[:, :, np.newaxis]
            
            return np.clip(result, 0, 255).astype(np.uint8)
        
        return VideoClip(make_frame, duration=clip.duration)
    
    def _grain(self, clip: VideoClip, amount: float = 0.2) -> VideoClip:
        """颗粒噪声"""
        def make_frame(t):
            frame = clip.get_frame(t)
            noise = np.random.normal(0, 255 * amount, frame.shape)
            result = frame + noise
            return np.clip(result, 0, 255).astype(np.uint8)
        
        return VideoClip(make_frame, duration=clip.duration)
    
    def _blur(self, clip: VideoClip, kernel_size: int = 5) -> VideoClip:
        """模糊效果"""
        def make_frame(t):
            frame = clip.get_frame(t)
            result = cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)
            return result
        
        return VideoClip(make_frame, duration=clip.duration)
    
    # 以下是其他风格的简化实现
    
    def _35mm_film(self, clip: VideoClip) -> VideoClip:
        """35mm胶片效果"""
        return self._film_grain(clip, intensity=0.2)
    
    def _halation(self, clip: VideoClip) -> VideoClip:
        """光晕效果"""
        return self._bloom(clip, threshold=180)
    
    def _anamorphic_flare(self, clip: VideoClip) -> VideoClip:
        """变形镜头光晕"""
        return self._bloom(clip, threshold=200)
    
    def _film_burn(self, clip: VideoClip) -> VideoClip:
        """胶片烧伤效果"""
        return self._vignette(clip, strength=0.7)
    
    def _datamosh(self, clip: VideoClip) -> VideoClip:
        """数据损坏效果"""
        return self._digital_noise(clip, amount=0.3)
    
    def _pixel_sort(self, clip: VideoClip) -> VideoClip:
        """像素排序"""
        return self._posterize(clip, levels=6)
    
    def _rgb_shift(self, clip: VideoClip) -> VideoClip:
        """RGB通道偏移"""
        return self._chromatic_aberration(clip, shift=8)
    
    def _screen_tear(self, clip: VideoClip) -> VideoClip:
        """屏幕撕裂"""
        return self._scan_lines(clip, spacing=5)
    
    def _vhs_effect(self, clip: VideoClip) -> VideoClip:
        """VHS效果"""
        clip = self._chromatic_aberration(clip, shift=3)
        clip = self._scan_lines(clip, spacing=4)
        return self._grain(clip, amount=0.15)
    
    def _crt_screen(self, clip: VideoClip) -> VideoClip:
        """CRT显示器效果"""
        clip = self._scan_lines(clip, spacing=2)
        return self._vignette(clip, strength=0.3)
    
    def _pastel_gradient(self, clip: VideoClip) -> VideoClip:
        """粉彩渐变"""
        def make_frame(t):
            frame = clip.get_frame(t)
            # 添加粉彩色调
            pastel = np.array([255, 200, 220], dtype=np.float32)
            result = frame * 0.7 + pastel * 0.3
            return np.clip(result, 0, 255).astype(np.uint8)
        
        return VideoClip(make_frame, duration=clip.duration)
    
    def _vhs_tracking(self, clip: VideoClip) -> VideoClip:
        """VHS跟踪线"""
        return self._scan_lines(clip, spacing=8)