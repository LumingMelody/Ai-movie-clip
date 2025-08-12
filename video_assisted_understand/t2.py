import cv2
import numpy as np
from skimage.exposure import match_histograms
from skimage import io, color, img_as_ubyte
import matplotlib.pyplot as plt
from collections import Counter

# 假设的Qwen接口，用于智能分析主题并推荐最合适的风格参考图像
def qwen_theme_analysis(theme_description, images_info):
    """
    模拟Qwen对主题的智能分析，并推荐最合适的风格参考图像。
    
    :param theme_description: 主题描述字符串
    :param images_info: 包含每张图像颜色风格信息的列表
    :return: 推荐的参考图像索引
    """
    # 简单示例：如果主题包含“冷”，则倾向于选择色调偏冷的图像
    cold_keywords = ["cold", "cool", "blue"]
    warm_keywords = ["warm", "hot", "red"]

    best_match_index = 0
    best_match_score = float('inf')  # 寻找最小差异

    for i, info in enumerate(images_info):
        mean_hue = info['hsv_stats']['mean_hue']
        if any(word in theme_description.lower() for word in cold_keywords):
            score = abs(mean_hue - 100)  # 蓝色区域
        elif any(word in theme_description.lower() for word in warm_keywords):
            score = abs(mean_hue - 20)   # 红色区域
        else:
            score = abs(mean_hue - 50)   # 中性

        if score < best_match_score:
            best_match_score = score
            best_match_index = i

    return best_match_index

class ColorStyleAnalyzer:
    def __init__(self, n_colors=5):
        self.n_colors = n_colors

    def load_image(self, image_path):
        """加载图像（BGR -> RGB）"""
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image

    def resize_image(self, image, max_size=800):
        h, w = image.shape[:2]
        scale = max_size / max(h, w)
        if scale < 1:
            new_w, new_h = int(w * scale), int(h * scale)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return image

    def get_dominant_colors(self, image):
        pixels = image.reshape(-1, 3)
        kmeans = KMeans(n_clusters=self.n_colors, n_init=10, random_state=42)
        kmeans.fit(pixels)
        colors = kmeans.cluster_centers_.astype(int)
        labels = kmeans.labels_
        count = Counter(labels)
        sorted_idx = np.argsort([count[i] for i in range(self.n_colors)])[::-1]
        dominant_colors = np.array(colors)[sorted_idx]
        color_freq = np.array([count[i] for i in range(self.n_colors)])[sorted_idx] / len(labels)
        return dominant_colors, color_freq

    def analyze_hsv_stats(self, image):
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        h_vals = hsv[:, :, 0].ravel()
        s_vals = hsv[:, :, 1].ravel()
        v_vals = hsv[:, :, 2].ravel()
        valid_pixels = (s_vals > 10) & (v_vals > 10)
        h_vals = h_vals[valid_pixels]
        s_vals = s_vals[valid_pixels]
        v_vals = v_vals[valid_pixels]

        mean_h = np.mean(h_vals)
        mean_s = np.mean(s_vals)
        mean_v = np.mean(v_vals)

        std_h = np.std(h_vals)
        std_s = np.std(s_vals)
        std_v = np.std(v_vals)

        return {
            'mean_hue': mean_h,
            'mean_sat': mean_s,
            'mean_val': mean_v,
            'std_hue': std_h,
            'std_sat': std_s,
            'std_val': std_v
        }

    def analyze(self, image_path):
        image = self.load_image(image_path)
        image = self.resize_image(image)

        dominant_colors, color_freq = self.get_dominant_colors(image)
        hsv_stats = self.analyze_hsv_stats(image)

        result = {
            'dominant_colors': dominant_colors,
            'color_frequencies': color_freq,
            'hsv_stats': hsv_stats,
            'image_shape': image.shape
        }
        return result

def apply_histogram_matching(source, reference):
    matched = match_histograms(source, reference, multichannel=True)
    return matched

def reinhard_color_transfer(source, target):
    source_lab = cv2.cvtColor(source, cv2.COLOR_RGB2LAB).astype("float32")
    target_lab = cv2.cvtColor(target, cv2.COLOR_RGB2LAB).astype("float32")

    (l_mean_src, l_std_src, a_mean_src, a_std_src, b_mean_src, b_std_src) = image_stats(source_lab)
    (l_mean_tar, l_std_tar, a_mean_tar, a_std_tar, b_mean_tar, b_std_tar) = image_stats(target_lab)

    lab_t = ((target_lab - [l_mean_tar, a_mean_tar, b_mean_tar]) /
             [l_std_tar, a_std_tar, b_std_tar]) * [l_std_src, a_std_src, b_std_src] + [l_mean_src, a_mean_src, b_mean_src]

    lab_t = np.clip(lab_t, 0, 255).astype(np.uint8)
    final = cv2.cvtColor(lab_t, cv2.COLOR_LAB2RGB)
    return final

def image_stats(image):
    (l, a, b) = cv2.split(image)
    (lMean, lStd) = (l.mean(), l.std())
    (aMean, aStd) = (a.mean(), a.std())
    (bMean, bStd) = (b.mean(), b.std())

    return (lMean, lStd, aMean, aStd, bMean, bStd)

def process_images(image_paths, theme_description, output_dir):
    analyzer = ColorStyleAnalyzer()
    images_info = []

    print("Analyzing images...")
    for path in image_paths:
        info = analyzer.analyze(path)
        images_info.append(info)

    # 使用Qwen进行主题分析，确定最佳参考图像
    ref_index = qwen_theme_analysis(theme_description, images_info)
    reference_image = analyzer.load_image(image_paths[ref_index])
    reference_image = analyzer.resize_image(reference_image)

    for i, path in enumerate(image_paths):
        print(f"Processing image {i+1}/{len(image_paths)}...")
        source_image = analyzer.load_image(path)
        source_image = analyzer.resize_image(source_image)

        matched = apply_histogram_matching(source_image, reference_image)
        result = reinhard_color_transfer(matched, reference_image)

        output_path = os.path.join(output_dir, f"processed_{os.path.basename(path)}")
        result = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
        cv2.imwrite(output_path, result)
        print(f"✅ 结果已保存至: {output_path}")

if __name__ == "__main__":
    import os

    # 输入多张图片路径
    image_paths = ["path/to/image1.jpg", "path/to/image2.jpg"]  # 替换为你的图片路径
    theme_description = "这是一个关于冬季旅行的故事，充满了冰雪和寒冷的气息。"  # 提供主题描述
    output_dir = "./output"  # 输出目录

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        process_images(image_paths, theme_description, output_dir)
    except Exception as e:
        print(f"❌ 错误: {e}")