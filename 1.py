from moviepy import ImageClip
clip = ImageClip("生成 AI 视频应用图标.png")
print(hasattr(clip, "resize"))  # 应该输出 True