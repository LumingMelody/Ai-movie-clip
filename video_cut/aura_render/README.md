# AuraRender 架构实现方案

## 核心理念
将视频创作分为两个完全独立的阶段：
1. **智能编排层（前端）**：负责所有智能决策，生成详细的执行脚本
2. **机械执行层（后端）**：根据脚本机械执行，无任何智能决策

## 目录结构

```
video_cut/aura_render/
├── intelligent_layer/          # 智能编排层
│   ├── video_types/           # 12种视频类型模板
│   │   ├── product_ad.py
│   │   ├── brand_promo.py
│   │   ├── knowledge_explain.py
│   │   ├── online_course.py
│   │   ├── short_drama.py
│   │   ├── music_mv.py
│   │   ├── vlog.py
│   │   ├── life_share.py
│   │   ├── micro_film.py
│   │   ├── concept_show.py
│   │   ├── game_video.py
│   │   └── training_video.py
│   ├── style_system/          # 风格系统
│   │   ├── realistic.py       # 写实系
│   │   ├── artistic.py       # 艺术系
│   │   ├── design.py          # 设计系
│   │   ├── cartoon.py         # 卡通系
│   │   └── futuristic.py     # 未来系
│   ├── resource_matcher.py    # 资源匹配器
│   ├── editing_planner.py     # 剪辑规划器
│   └── script_generator.py    # 脚本生成器
├── execution_layer/           # 机械执行层
│   ├── script_parser.py       # 脚本解析器
│   ├── resource_loader.py     # 资源加载器
│   ├── timeline_executor.py   # 时间轴执行器
│   ├── effect_applier.py      # 特效应用器
│   └── render_engine.py       # 渲染引擎
├── ai_generators/             # AI生成器（集成万相等）
│   ├── image_generator.py
│   ├── video_generator.py
│   ├── audio_generator.py
│   └── text_generator.py
└── templates/                 # 脚本模板
    └── execution_script.json
```

## 执行脚本格式

```json
{
  "version": "1.0",
  "project": {
    "id": "aura_001",
    "type": "product_advertisement",
    "style": {
      "category": "futuristic",
      "subtype": "cyberpunk"
    },
    "duration": 30,
    "resolution": "1920x1080",
    "fps": 30
  },
  "resources": {
    "videos": [
      {
        "id": "vid_001",
        "source": "ai_generated",
        "params": {
          "model": "animate_diff",
          "prompt": "product rotating 360 degrees, cyberpunk style"
        },
        "duration": 5
      }
    ],
    "images": [
      {
        "id": "img_001",
        "source": "oss://path/to/logo.png"
      }
    ],
    "audio": [
      {
        "id": "bgm_001",
        "source": "ai_generated",
        "params": {
          "model": "musicgen",
          "style": "electronic_tech"
        }
      }
    ]
  },
  "timeline": [
    {
      "start": 0,
      "end": 5,
      "layers": [
        {
          "type": "video",
          "resource_id": "vid_001",
          "effects": [
            {
              "type": "glow",
              "intensity": 0.8
            }
          ],
          "transform": {
            "scale": 1.2,
            "position": [960, 540]
          }
        },
        {
          "type": "text",
          "content": "智能手表X",
          "style": {
            "font": "futura",
            "size": 72,
            "color": "#00FFFF",
            "animation": "fade_in"
          }
        }
      ],
      "transition_out": {
        "type": "glitch",
        "duration": 0.5
      }
    }
  ],
  "global_effects": {
    "color_grading": "cyberpunk_preset",
    "filters": ["digital_noise", "scan_lines"]
  }
}
```

## 工作流程

1. **用户输入** → 智能编排层
2. **类型识别** → 选择对应的视频类型模板
3. **风格匹配** → 应用风格系统
4. **资源决策** → 决定使用现有素材或AI生成
5. **剪辑规划** → 确定每个片段的时长、特效等
6. **脚本生成** → 输出完整的执行脚本
7. **脚本执行** → 机械执行层按脚本渲染
8. **输出视频** → 最终成品

## 关键优势

- **完全解耦**：前后端通过脚本接口通信
- **可预测性**：执行结果完全由脚本决定
- **易于调试**：可以单独调试脚本生成或执行
- **高性能**：执行层可专注于渲染优化