import random
from moviepy import VideoClip,concatenate_videoclips

from core.cliptransition.easy_clip_transitions import (
    black_transition, crossfade_transition, circular_crossfadein_transition,
    blinds_transition, slide_transition, zoom_transition,
    rectangular_shrink_transition, directional_transition, rotate_transition,
    flash_transition
)


# 过渡特效池（支持权重控制 + 参数随机化）
transitions = [
    {
        "name": "black",
        "func": black_transition,
        "weight": 3,
        "params": {
            "duration": lambda: random.uniform(0.3, 0.7),
            "position": lambda: random.choice(["center", "top", "bottom"])
        }
    },
    {
        "name": "crossfade",
        "func": crossfade_transition,
        "weight": 4,
        "params": {
            "duration": lambda: random.uniform(0.3, 0.7)
        }
    },
    {
        "name": "circular_crossfadein",
        "func": circular_crossfadein_transition,
        "weight": 2,
        "params": {
            "duration": lambda: random.uniform(0.3, 0.7)
        }
    },
    {
        "name": "blinds",
        "func": blinds_transition,
        "weight": 2,
        "params": {
            "duration": lambda: random.uniform(0.3, 0.7),
            "num_blinds": lambda: random.randint(3, 8),
            "direction": lambda: random.choice(["vertical", "horizontal"])
        }
    },
    {
        "name": "slide",
        "func": slide_transition,
        "weight": 3,
        "params": {
            "duration": lambda: random.uniform(0.3, 0.7),
            "direction": lambda: random.choice(["left", "right", "up", "down"])
        }
    },
    {
        "name": "zoom",
        "func": zoom_transition,
        "weight": 2,
        "params": {
            "duration": lambda: random.uniform(0.3, 0.7)
        }
    },
    {
        "name": "shrink",
        "func": rectangular_shrink_transition,
        "weight": 1,
        "params": {
            "duration": lambda: random.uniform(0.3, 0.7)
        }
    },
    {
        "name": "directional",
        "func": directional_transition,
        "weight": 1,
        "params": {
            "duration": lambda: random.uniform(0.3, 0.7)
        }
    },
    {
        "name": "rotate",
        "func": rotate_transition,
        "weight": 2,
        "params": {
            "duration": lambda: random.uniform(0.3, 0.7)
        }
    },
    {
        "name": "flash",
        "func": flash_transition,
        "weight": 1,
        "params": {
            "duration": lambda: random.uniform(0.3, 0.7)
        }
    },
]


def apply_random_transition(clipA: VideoClip, clipB: VideoClip, duration=0.5):
    """
    随机选择一个过渡效果，并应用到 clipA 和 clipB 之间。
    
    参数:
        clipA (VideoClip): 第一个剪辑
        clipB (VideoClip): 第二个剪辑
        duration (float): 默认过渡时长
    
    返回:
        VideoClip: 合成后的剪辑
    """
    names = [t["name"] for t in transitions]
    weights = [t["weight"] for t in transitions]
    selected_idx = random.choices(range(len(transitions)), weights=weights, k=1)[0]
    selected = transitions[selected_idx]

    print(f"Applying Transition: {selected['name']}")

    # 构造参数
    params = {}
    for key, value_gen in selected.get("params", {}).items():
        if callable(value_gen):
            params[key] = value_gen()
        else:
            params[key] = value_gen

    # 确保 clipB 存在
    if clipB is None:
        raise ValueError("clipB 不能为 None")

    # 调用过渡函数
    transition_func = selected["func"]
    try:
        result_clip = transition_func(clipA, clipB, **params)
    except Exception as e:
        print(f"[ERROR] Transition failed: {e}, falling back to simple concat")
        result_clip = concatenate_videoclips([clipA, clipB])

    return result_clip