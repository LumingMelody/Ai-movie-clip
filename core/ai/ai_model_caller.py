# -*- coding: utf-8 -*-
"""
AI模型调用器 - 重构版本
功能：支持通义千问等大语言模型，使用OpenAI兼容格式
"""

import json
import time
import requests
import re
import os
from typing import Dict, Any, Optional, List

from core.utils.config_manager import config, ErrorHandler
from core.utils.env_config import get_dashscope_api_key


class AIModelCaller:
    """AI模型调用器 - 重构版本"""

    def __init__(self, api_key: str = None, model: str = None):
        """
        初始化AI模型调用器

        Args:
            api_key: API密钥，如果为None则从配置加载
            model: 模型名称，默认使用配置中的模型
        """
        # 加载配置
        self.ai_config = config.get_config('ai')
        
        # 优先使用传入的api_key，其次从环境变量获取
        self.api_key = api_key or get_dashscope_api_key()
        self.model = model or self.ai_config['default_model']
        self.base_url = self.ai_config['base_url']
        self.max_retries = self.ai_config['max_retries']
        self.timeout = self.ai_config['timeout']
        self.supported_models = self.ai_config['supported_models']

        self._validate_model()

    def _validate_model(self):
        """验证模型是否支持"""
        if self.model not in self.supported_models:
            ErrorHandler.log_warning(f"{self.model} 不在支持的模型列表中")
            print(f"支持的模型: {', '.join(self.supported_models)}")

    def generate_editing_plan(self, prompt: str, use_local: bool = False) -> Dict[str, Any]:
        """
        生成剪辑计划

        Args:
            prompt: 输入提示词
            use_local: 是否强制使用本地策略

        Returns:
            Dict: 剪辑计划
        """
        if use_local or not self.api_key:
            if not self.api_key:
                ErrorHandler.log_warning("未配置API密钥，使用本地策略")
            return self._generate_local_plan(prompt)

        # 在线调用，带重试机制
        return self._try_online_generation(prompt)
    
    def _try_online_generation(self, prompt: str) -> Dict[str, Any]:
        """尝试在线生成，带重试机制"""
        for attempt in range(self.max_retries):
            try:
                print(f"🤖 正在调用{self.model} API... (尝试 {attempt + 1}/{self.max_retries})")
                return self._call_qwen_openai_compatible(prompt)

            except requests.exceptions.Timeout as e:
                if not self._handle_retry("API调用超时", e, attempt):
                    break
            except requests.exceptions.RequestException as e:
                if not self._handle_retry("网络请求错误", e, attempt):
                    break
            except Exception as e:
                if not self._handle_retry("API调用", e, attempt):
                    break
        
        ErrorHandler.log_warning("所有在线尝试都失败，降级到本地策略")
        return self._generate_local_plan(prompt)
    
    def _handle_retry(self, error_type: str, error: Exception, attempt: int) -> bool:
        """处理重试逻辑"""
        ErrorHandler.handle_api_error(error_type, error, attempt + 1)
        
        if attempt < self.max_retries - 1:
            wait_time = (attempt + 1) * 2  # 递增等待
            print(f"等待 {wait_time} 秒后重试...")
            time.sleep(wait_time)
            return True
        return False

    def _call_qwen_openai_compatible(self, prompt: str) -> Dict[str, Any]:
        """调用Qwen API - OpenAI兼容格式"""

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        # 🔥 增强的系统提示词 - 支持多片段策略
        system_prompt = """你是一个专业的视频剪辑AI助手。请根据用户提供的视频分析结果，生成JSON格式的多片段剪辑策略。

        ### 🎯 核心策略：智能多片段组合
        你的任务是将长视频智能拆分成多个精彩片段，然后组合成目标时长的短视频。这比单纯截取一个连续段落更加智能和有趣。

        ### 📊 输入数据格式：
        {
            "metadata": { 
                "duration": <float>,     # 视频总时长（秒）
                "width": <int>, "height": <int>, 
                "fps": <float>
            },
            "classification": {
                "content_type": "广告宣传片类",  # 教育教学/广告宣传/直播录播/人声剧情/动作运动等
                "mood": "激昂",               # 紧张/宁静/欢快/感动等
                "style": "抖音风",            # 抖音风/Vlog风/电影感/纪录片风等
                "purpose": "社交媒体"         # 教学培训/企业宣传/社交媒体/个人记录等
            },
            "scene_changes": [[start1, end1], [start2, end2], ...],  # 场景切换时间戳
            "speech_text": "完整的语音识别文本...",
            "speech_timestamps": {
                "segments": [
                    {"start": 10.5, "end": 13.2, "text": "句子1", "duration": 2.7},
                    {"start": 13.5, "end": 16.8, "text": "句子2", "duration": 3.3}
                ],
                "best_segments": [  # 预分析的最佳语音片段
                    {"start": 120.0, "end": 150.0, "duration": 30.0, "word_density": 1.5},
                    {"start": 200.0, "end": 225.0, "duration": 25.0, "word_density": 1.3}
                ]
            },
            "highlights": [  # 系统预推荐的精彩时间段
                {"start_time": 45.0, "end_time": 60.0, "reason": "场景1", "confidence": 0.8},
                {"start_time": 120.0, "end_time": 140.0, "reason": "高互动片段", "confidence": 0.9}
            ],
            "objects_detected": {"person": {"count": 15, "avg_confidence": 0.85}},
            "face_detected": true,
            "music_analysis": {"tempo": 128, "energy": 0.75, "chroma_mean": 0.6}
        }

        ### 🧠 多片段策略生成指南：

        #### 1. 片段选择策略：
        - **开头吸引** (3-8秒): 选择最吸引人的开场，通常是高能量或关键信息
        - **核心内容** (15-20秒): 选择2-3个核心片段，保持逻辑连贯
        - **精彩收尾** (3-7秒): 强有力的结尾，留下深刻印象

        #### 2. 不同内容类型的多片段策略：
        - **教育教学类**: 开场问题 + 核心知识点 + 总结回顾
        - **广告宣传类**: 产品亮相 + 核心卖点 + 行动召唤
        - **直播录播类**: 开场互动 + 高潮时刻 + 精彩反应
        - **人声剧情类**: 冲突设置 + 情感高潮 + 结果揭晓
        - **动作运动类**: 准备动作 + 关键时刻 + 结果展示

        #### 3. 片段时长分配建议：
        - 30秒目标：3-5个片段，每个5-10秒
        - 60秒目标：4-7个片段，每个8-15秒
        - 保持节奏感，避免单个片段过长

        ### 📦 新的输出格式 - 多片段策略：
        {
            "target_duration": 30,
            "strategy_type": "multi_segment",
            "actions": [
                {
                    "action": "extract_segment",
                    "start": 10.5,
                    "end": 18.2,
                    "duration": 7.7,
                    "reason": "开场吸引：产品亮相，抓住注意力",
                    "segment_role": "opening",
                    "priority": 1
                },
                {
                    "action": "extract_segment", 
                    "start": 45.0,
                    "end": 58.0,
                    "duration": 13.0,
                    "reason": "核心内容：展示主要功能特点",
                    "segment_role": "main_content",
                    "priority": 1
                },
                {
                    "action": "extract_segment",
                    "start": 120.5,
                    "end": 129.0, 
                    "duration": 8.5,
                    "reason": "精彩收尾：用户好评反馈",
                    "segment_role": "closing",
                    "priority": 1
                },
                {
                    "action": "apply_transitions",
                    "transition_type": "crossfade",
                    "duration": 0.5,
                    "between_segments": true,
                    "reason": "片段间平滑过渡"
                },
                {
                    "action": "apply_filter",
                    "filter_name": "enhance",
                    "intensity": 0.3,
                    "apply_to": "all_segments",
                    "reason": "整体视觉增强"
                }
            ],
            "segments_summary": {
                "total_segments": 3,
                "estimated_duration": 29.2,
                "coverage_ratio": 0.026  // 覆盖原视频的比例
            },
            "metadata": {
                "description": "智能多片段组合策略：开场吸引+核心展示+精彩收尾",
                "confidence": 0.9,
                "strategy_reasoning": "根据广告宣传片的特点，选择最具吸引力的开场、核心卖点展示和用户反馈收尾，形成完整的营销闭环"
            }
        }

        ### 🎬 新增的Action类型：

        #### extract_segment（核心新增）：
        - **作用**: 提取特定时间段的视频片段
        - **必需参数**: start, end, duration, reason
        - **可选参数**: segment_role (opening/main_content/supporting/closing), priority (1-3)
        - **segment_role说明**:
          - opening: 开场片段，用于吸引注意力
          - main_content: 主要内容，核心信息
          - supporting: 支撑内容，补充说明
          - closing: 收尾片段，强化印象

        #### apply_transitions（增强）：
        - **between_segments**: true 表示应用于片段之间
        - **transition_type**: crossfade, slide, zoom, flash等

        #### apply_filter（增强）：
        - **apply_to**: "all_segments" | "segment_1" | "segment_2" 等

        ### 💡 策略生成要点：
        1. **分析输入数据**: 充分利用scene_changes、speech_timestamps、highlights等信息
        2. **保持逻辑性**: 确保选择的片段能形成完整的故事线
        3. **控制总时长**: 所有extract_segment的duration总和应接近target_duration
        4. **考虑转场时间**: 预留0.5-1秒的转场时间
        5. **优先级排序**: 重要片段priority=1，次要片段priority=2-3

        ### 🎯 输出要求：
        - 必须包含3-7个extract_segment动作
        - 总estimated_duration应在target_duration的±10%范围内
        - 每个segment必须有明确的reason和segment_role
        - 提供strategy_reasoning解释选择逻辑

        请严格按照上述JSON格式返回多片段剪辑策略，不要包含任何解释文字，仅返回JSON内容。"""

        # OpenAI兼容格式的请求体
        data = self._build_request_data(system_prompt, prompt)

        return self._make_api_request(headers, data, prompt)
    
    def _build_request_data(self, system_prompt: str, prompt: str) -> Dict[str, Any]:
        """构建请求数据"""
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt + "\n\n请生成智能多片段剪辑策略。严格按照JSON格式返回。"}
            ],
            "max_tokens": self.ai_config['max_tokens'],
            "temperature": self.ai_config['temperature']
        }
    
    def _make_api_request(self, headers: Dict[str, str], data: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """执行API请求"""
        url = f"{self.base_url}/chat/completions"
        
        print(f"📡 正在调用 {self.model} API...")
        response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
        
        if response.status_code == 200:
            return self._process_successful_response(response, prompt)
        else:
            raise Exception(self._build_error_message(response))
    
    def _process_successful_response(self, response, prompt: str) -> Dict[str, Any]:
        """处理成功的API响应"""
        result = response.json()
        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        print(f"AI策略: {content[:200]}...")  # 只显示前200字符
        ErrorHandler.log_success(f"API调用成功，响应长度: {len(content)} 字符")
        
        # 解析AI响应
        plan = self._parse_ai_response(content)
        if plan and self._validate_multi_segment_plan(plan):
            ErrorHandler.log_success("AI策略解析成功")
            return plan
        else:
            ErrorHandler.log_warning("策略验证失败，使用本地策略")
            return self._generate_local_multi_segment_plan(prompt)
    
    def _build_error_message(self, response) -> str:
        """构建错误消息"""
        error_msg = f"API调用失败: {response.status_code}"
        if response.text:
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail.get('error', {}).get('message', response.text)}"
            except:
                error_msg += f" - {response.text}"
        return error_msg

    def _validate_multi_segment_plan(self, plan: Dict[str, Any]) -> bool:
        """验证多片段剪辑计划的格式是否正确"""
        try:
            # 基础验证
            if not self._validate_plan(plan):
                return False

            # 检查是否有extract_segment动作
            actions = plan.get('actions', [])
            extract_segments = [a for a in actions if a.get('action') == 'extract_segment']

            if len(extract_segments) < 2:
                print(f"⚠️ 多片段策略至少需要2个片段，当前只有{len(extract_segments)}个")
                return False

            # 检查片段参数完整性
            for segment in extract_segments:
                required_fields = ['start', 'end', 'duration', 'reason']
                if not all(field in segment for field in required_fields):
                    print(f"⚠️ 片段缺少必需字段: {segment}")
                    return False

            # 检查总时长是否合理
            total_duration = sum(s.get('duration', 0) for s in extract_segments)
            target_duration = plan.get('target_duration', 30)

            if abs(total_duration - target_duration) > target_duration * 0.2:  # 允许20%误差
                print(f"⚠️ 总时长偏差过大: 目标{target_duration}s, 实际{total_duration}s")
                return False

            print(f"✅ 多片段策略验证通过: {len(extract_segments)}个片段, 总时长{total_duration:.1f}s")
            return True

        except Exception as e:
            print(f"⚠️ 多片段策略验证异常: {e}")
            return False

    def _generate_local_multi_segment_plan(self, prompt: str) -> Dict[str, Any]:
        """本地生成多片段剪辑计划（增强版）"""
        print("🏠 使用本地智能多片段策略")

        # 从prompt中提取目标时长和视频信息
        target_duration = 30
        video_duration = 1200  # 默认20分钟，应该从prompt中解析

        # 解析视频时长
        duration_match = re.search(r'"duration":\s*(\d+\.?\d*)', prompt)
        if duration_match:
            video_duration = float(duration_match.group(1))

        # 解析目标时长
        target_match = re.search(r'目标时长[：:]\s*(\d+)', prompt)
        if target_match:
            target_duration = int(target_match.group(1))

        # 智能片段分配策略
        if video_duration <= 60:
            # 短视频：选择2-3个片段
            segments = [
                {"start": 5, "duration": target_duration * 0.4, "role": "opening"},
                {"start": video_duration * 0.6, "duration": target_duration * 0.6, "role": "main_content"}
            ]
        elif video_duration <= 300:
            # 中长视频：选择3-4个片段
            segments = [
                {"start": 10, "duration": target_duration * 0.25, "role": "opening"},
                {"start": video_duration * 0.3, "duration": target_duration * 0.4, "role": "main_content"},
                {"start": video_duration * 0.75, "duration": target_duration * 0.35, "role": "closing"}
            ]
        else:
            # 长视频：选择4-5个片段
            segments = [
                {"start": 15, "duration": target_duration * 0.2, "role": "opening"},
                {"start": video_duration * 0.2, "duration": target_duration * 0.3, "role": "main_content"},
                {"start": video_duration * 0.5, "duration": target_duration * 0.25, "role": "supporting"},
                {"start": video_duration * 0.8, "duration": target_duration * 0.25, "role": "closing"}
            ]

        # 生成extract_segment动作
        actions = []
        for i, seg in enumerate(segments):
            start = seg["start"]
            duration = seg["duration"]
            end = start + duration

            # 确保不超出视频范围
            if end > video_duration:
                end = video_duration
                duration = end - start

            if duration > 2:  # 只添加有意义长度的片段
                actions.append({
                    "action": "extract_segment",
                    "start": start,
                    "end": end,
                    "duration": duration,
                    "reason": f"本地策略：{seg['role']}片段",
                    "segment_role": seg["role"],
                    "priority": 1
                })

        # 添加转场和滤镜
        actions.append({
            "action": "apply_transitions",
            "transition_type": "crossfade",
            "duration": 0.5,
            "between_segments": True,
            "reason": "片段间平滑过渡"
        })

        # 根据内容类型添加合适的滤镜
        if '抖音' in prompt or '社交' in prompt:
            actions.append({
                "action": "apply_filter",
                "filter_name": "vibrant",
                "intensity": 0.4,
                "apply_to": "all_segments",
                "reason": "社交媒体风格增强"
            })
        else:
            actions.append({
                "action": "apply_filter",
                "filter_name": "enhance",
                "intensity": 0.3,
                "apply_to": "all_segments",
                "reason": "整体视觉增强"
            })

        # 计算总时长
        total_duration = sum(a.get('duration', 0) for a in actions if a.get('action') == 'extract_segment')
        segment_count = len([a for a in actions if a.get('action') == 'extract_segment'])

        return {
            "target_duration": target_duration,
            "strategy_type": "multi_segment",
            "actions": actions,
            "segments_summary": {
                "total_segments": segment_count,
                "estimated_duration": total_duration,
                "coverage_ratio": round(total_duration / video_duration, 3)
            },
            "metadata": {
                "description": f"本地多片段策略：{segment_count}个智能选择的片段",
                "confidence": 0.7,
                "source": "local_multi_segment",
                "strategy_reasoning": "基于视频时长和内容特点，智能选择开头、核心和结尾片段"
            }
        }

    def _parse_ai_response(self, content: str) -> Optional[Dict[str, Any]]:
        """解析AI响应，提取JSON格式的剪辑计划"""

        # 方法1: 直接解析
        try:
            plan = json.loads(content.strip())
            if self._validate_plan(plan):
                return plan
        except json.JSONDecodeError:
            pass

        # 方法2: 提取JSON块
        json_plan = self._extract_json_from_text(content)
        if json_plan and self._validate_plan(json_plan):
            return json_plan

        # 方法3: 智能提取关键信息
        return self._extract_plan_from_text(content)

    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本中提取JSON"""
        try:
            # 寻找JSON块的多种模式
            patterns = [
                r'```json\s*(.*?)\s*```',  # ```json ... ```
                r'```\s*(.*?)\s*```',  # ``` ... ```
                r'({.*?})',  # { ... }
            ]

            for pattern in patterns:
                matches = re.findall(pattern, text, re.DOTALL)
                for match in matches:
                    try:
                        # 清理文本
                        json_str = match.strip()
                        if json_str.startswith('{') and json_str.endswith('}'):
                            plan = json.loads(json_str)
                            if isinstance(plan, dict):
                                return plan
                    except json.JSONDecodeError:
                        continue

            # 尝试找到完整的JSON对象
            brace_count = 0
            start_idx = -1
            for i, char in enumerate(text):
                if char == '{':
                    if brace_count == 0:
                        start_idx = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and start_idx != -1:
                        json_str = text[start_idx:i + 1]
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError:
                            continue

            return None
        except Exception:
            return None

    def _extract_plan_from_text(self, text: str) -> Dict[str, Any]:
        """从自然语言文本中提取剪辑计划"""

        # 提取目标时长
        target_duration = 30
        duration_patterns = [
            r'目标时长[：:]\s*(\d+)',
            r'时长[：:]\s*(\d+)',
            r'(\d+)\s*秒'
        ]

        for pattern in duration_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    target_duration = int(match.group(1))
                    break
                except:
                    pass

        # 根据文本内容推断操作
        actions = []

        # 检测剪切操作
        if any(keyword in text for keyword in ['剪切', '裁剪', '截取', '时长']):
            actions.append({
                "action": "cut",
                "target_duration": target_duration,
                "preserve_important": True,
                "reason": "剪切，根据要求保留内容"
            })

        # 检测滤镜操作
        if any(keyword in text for keyword in ['滤镜', '增强', '美化', '调色']):
            actions.append({
                "action": "apply_filter",
                "filter_name": "enhance",
                "intensity": 0.3,
                "reason": "AI建议应用增强滤镜"
            })

        # 检测转场操作
        if any(keyword in text for keyword in ['转场', '过渡', '衔接']):
            actions.append({
                "action": "apply_transitions",
                "transition_type": "fade",
                "duration": 0.5,
                "reason": "AI建议添加转场效果"
            })

        # 如果没有检测到任何操作，添加默认操作
        if not actions:
            actions.append({
                "action": "cut",
                "target_duration": target_duration,
                "preserve_important": True,
                "reason": "剪切，根据要求保留内容"
            })

        return {
            "target_duration": target_duration,
            "actions": actions,
            "metadata": {
                "description": f"从AI文本响应提取的剪辑策略: {text[:100]}...",
                "confidence": 0.6,
                "source": "text_extraction"
            }
        }

    def _validate_plan(self, plan: Dict[str, Any]) -> bool:
        """验证剪辑计划的格式是否正确"""
        try:
            # 检查必需字段
            if not isinstance(plan, dict):
                return False

            # target_duration 应该是数字
            if 'target_duration' in plan:
                if not isinstance(plan['target_duration'], (int, float)):
                    return False

            # actions 应该是列表
            if 'actions' in plan:
                if not isinstance(plan['actions'], list):
                    return False

                # 检查每个action的格式
                for action in plan['actions']:
                    if not isinstance(action, dict) or 'action' not in action:
                        return False

            return True

        except Exception:
            return False

    def _generate_local_plan(self, prompt: str) -> Dict[str, Any]:
        """本地生成剪辑计划（备用方案）"""
        print("🏠 使用本地智能策略生成剪辑计划")

        # 从prompt中提取目标时长
        target_duration = 30
        duration_patterns = [
            r'目标时长[：:]\s*(\d+)',
            r'时长[：:]\s*(\d+)',
            r'(\d+)\s*秒'
        ]

        for pattern in duration_patterns:
            match = re.search(pattern, prompt)
            if match:
                try:
                    target_duration = int(match.group(1))
                    break
                except:
                    pass

        # 根据内容类型生成不同策略
        actions = []

        if '企业' in prompt or '商务' in prompt:
            # 企业风格
            actions = [
                {
                    "action": "cut",
                    "target_duration": target_duration,
                    "preserve_important": True,
                    "reason": "剪切，根据要求保留内容"
                },
                {
                    "action": "apply_filter",
                    "filter_name": "professional",
                    "intensity": 0.2,
                    "reason": "应用专业风格滤镜"
                }
            ]
        elif '抖音' in prompt or '社交' in prompt:
            # 社交媒体风格
            actions = [
                {
                    "action": "cut",
                    "target_duration": target_duration,
                    "preserve_important": True,
                    "reason": "快节奏剪切适合社交媒体"
                },
                {
                    "action": "apply_filter",
                    "filter_name": "vibrant",
                    "intensity": 0.4,
                    "reason": "应用鲜艳滤镜增加吸引力"
                }
            ]
        else:
            # 通用策略
            actions = [
                {
                    "action": "cut",
                    "target_duration": target_duration,
                    "preserve_important": True,
                    "reason": "剪切，根据要求保留内容"
                }
            ]

        return {
            "target_duration": target_duration,
            "actions": actions,
            "metadata": {
                "description": f"本地生成的智能剪辑策略 - 目标时长{target_duration}秒",
                "confidence": 0.7,
                "source": "local_generation"
            }
        }

    def test_connection(self) -> Dict[str, Any]:
        """测试API连接"""

        if not self.api_key:
            return {
                "status": "failed",
                "recommended_mode": "local",
                "error": "未配置API密钥"
            }

        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            # 使用最便宜的模型测试
            test_data = {
                "model": "qwen-turbo",
                "messages": [
                    {"role": "user", "content": "测试连接"}
                ],
                "max_tokens": 5
            }

            url = f"{self.base_url}/chat/completions"
            response = requests.post(url, json=test_data, headers=headers, timeout=10)

            if response.status_code == 200:
                return {
                    "status": "success",
                    "recommended_mode": "online",
                    "model": self.model
                }
            else:
                error_detail = ""
                try:
                    error_info = response.json()
                    error_detail = error_info.get('error', {}).get('message', response.text)
                except:
                    error_detail = response.text

                return {
                    "status": "failed",
                    "recommended_mode": "local",
                    "error": f"HTTP {response.status_code}: {error_detail}"
                }

        except requests.exceptions.Timeout:
            return {
                "status": "failed",
                "recommended_mode": "local",
                "error": "连接超时"
            }
        except Exception as e:
            return {
                "status": "failed",
                "recommended_mode": "local",
                "error": str(e)
            }

    def call_model(self, prompt: str) -> str:
        """
        兼容旧版本的方法 - 直接调用模型返回文本

        Args:
            prompt: 输入提示词

        Returns:
            str: 模型返回的文本
        """
        try:
            plan = self.generate_editing_plan(prompt, use_local=False)
            return json.dumps(plan, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"调用失败: {str(e)}"

    def set_model(self, model: str) -> bool:
        """
        设置使用的模型

        Args:
            model: 模型名称

        Returns:
            bool: 是否设置成功
        """
        if model in self.supported_models:
            self.model = model
            print(f"✅ 模型已设置为: {model}")
            return True
        else:
            print(f"❌ 不支持的模型: {model}")
            print(f"支持的模型: {', '.join(self.supported_models)}")
            return False

    def get_available_models(self) -> List[str]:
        """获取支持的模型列表"""
        return self.supported_models.copy()


# 便捷函数
def test_ai_connection(api_key: str = None) -> Dict[str, Any]:
    """测试AI连接的便捷函数"""
    caller = AIModelCaller(api_key=api_key)
    return caller.test_connection()


def quick_generate_plan(prompt: str, api_key: str = None, model: str = "qwen-plus") -> Dict[str, Any]:
    """快速生成剪辑计划的便捷函数"""
    caller = AIModelCaller(api_key=api_key, model=model)
    return caller.generate_editing_plan(prompt)


if __name__ == "__main__":
    # 测试代码
    print("🧪 测试 AIModelCaller...")

    caller = AIModelCaller()

    # 测试连接
    result = caller.test_connection()
    print(f"连接测试结果: {result}")

    # 测试生成计划
    test_prompt = """
    视频信息：
    - 时长: 120秒
    - 内容类型: 企业宣传
    - 目标时长: 30秒
    - 目标风格: 企业风

    请生成剪辑策略。
    """

    plan = caller.generate_editing_plan(test_prompt)
    print(f"生成的剪辑计划: {json.dumps(plan, ensure_ascii=False, indent=2)}")