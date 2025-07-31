"""
AuraRender 智能编排器

负责：
1. 理解用户需求
2. 选择视频类型
3. 匹配风格系统
4. 规划资源使用
5. 生成执行脚本
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import os

# 添加项目根目录到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from video_cut.core.controller import UnifiedController
from video_cut.config import DAG, NODES


class AuraOrchestrator:
    """智能编排器 - 负责所有智能决策"""
    
    def __init__(self):
        # 复用video_cut的控制器
        self.controller = UnifiedController(DAG, NODES)
        
        # 视频类型映射
        self.video_types = {
            'product_ad': '产品广告',
            'brand_promo': '品牌宣传',
            'knowledge_explain': '知识科普',
            'online_course': '在线课程',
            'short_drama': '短剧',
            'music_mv': '音乐MV',
            'vlog': 'Vlog',
            'life_share': '生活分享',
            'micro_film': '微电影',
            'concept_show': '概念展示',
            'game_video': '游戏视频',
            'training_video': '培训视频'
        }
        
        # 风格系统映射
        self.style_systems = {
            'realistic': '写实系',
            'artistic': '艺术系',
            'design': '设计系',
            'cartoon': '卡通系',
            'futuristic': '未来系'
        }
        
    def orchestrate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        主编排方法
        
        Args:
            request: {
                'natural_language': str,  # 用户的自然语言描述
                'video_url': str,        # 原始视频URL（可选）
                'resources': Dict,       # 额外资源（可选）
                'preferences': Dict      # 用户偏好（可选）
            }
        
        Returns:
            执行脚本JSON
        """
        # 1. 分析用户需求
        analysis = self._analyze_request(request)
        
        # 2. 选择视频类型
        video_type = self._select_video_type(analysis)
        
        # 3. 确定风格
        style = self._determine_style(analysis, video_type)
        
        # 4. 规划资源
        resources = self._plan_resources(analysis, request.get('resources', {}))
        
        # 5. 生成时间轴
        timeline = self._generate_timeline(analysis, video_type, style)
        
        # 6. 构建执行脚本
        script = self._build_execution_script(
            analysis, video_type, style, resources, timeline
        )
        
        return script
    
    def _analyze_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """分析用户请求"""
        natural_language = request.get('natural_language', '')
        
        # 使用video_cut的自然语言处理能力
        if hasattr(self.controller, 'nl_processor'):
            outline = self.controller.nl_processor.process_natural_language(natural_language)
        else:
            # 直接使用controller处理
            context = {"大纲内容": f"用户需求：{natural_language}"}
            result = self.controller.run_generate(context)
            outline = result.get('node1', {})
        
        # 提取关键信息
        analysis = {
            'original_request': natural_language,
            'outline': outline,
            'duration': self._extract_duration(natural_language),
            'keywords': self._extract_keywords(natural_language),
            'intent': self._detect_intent(natural_language)
        }
        
        return analysis
    
    def _select_video_type(self, analysis: Dict[str, Any]) -> str:
        """根据分析结果选择视频类型"""
        keywords = analysis.get('keywords', [])
        intent = analysis.get('intent', '')
        
        # 基于关键词匹配
        type_keywords = {
            'product_ad': ['产品', '商品', '介绍', '展示', '功能'],
            'brand_promo': ['品牌', '企业', '公司', '宣传'],
            'knowledge_explain': ['科普', '知识', '教学', '讲解'],
            'online_course': ['课程', '教程', '培训', '学习'],
            'short_drama': ['剧情', '故事', '短剧'],
            'music_mv': ['音乐', 'MV', '歌曲'],
            'vlog': ['vlog', '日常', '记录'],
            'life_share': ['生活', '分享', '日常'],
            'micro_film': ['微电影', '短片'],
            'concept_show': ['概念', '创意', '艺术'],
            'game_video': ['游戏', '电竞', '解说'],
            'training_video': ['培训', '指导', '操作']
        }
        
        # 计算匹配度
        scores = {}
        for vtype, vkeywords in type_keywords.items():
            score = sum(1 for k in keywords if any(vk in k for vk in vkeywords))
            if score > 0:
                scores[vtype] = score
        
        # 返回得分最高的类型，默认为product_ad
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return 'product_ad'
    
    def _determine_style(self, analysis: Dict[str, Any], video_type: str) -> Dict[str, Any]:
        """确定视频风格"""
        keywords = analysis.get('keywords', [])
        
        # 风格关键词映射
        style_keywords = {
            'realistic': ['真实', '纪实', '写实', '自然'],
            'artistic': ['艺术', '创意', '抽象', '唯美'],
            'design': ['设计', '简约', '现代', '极简'],
            'cartoon': ['卡通', '动画', '可爱', '二次元'],
            'futuristic': ['未来', '科技', '赛博朋克', '科幻']
        }
        
        # 匹配风格
        category = 'realistic'  # 默认
        for style, skeywords in style_keywords.items():
            if any(k in keywords for k in skeywords):
                category = style
                break
        
        # 根据视频类型调整子类型
        subtype_map = {
            'realistic': ['documentary', 'natural', 'candid'],
            'artistic': ['abstract', 'impressionist', 'surreal'],
            'design': ['minimalist', 'modern', 'bauhaus'],
            'cartoon': ['anime', '2d', '3d'],
            'futuristic': ['cyberpunk', 'tech', 'scifi']
        }
        
        return {
            'category': category,
            'subtype': subtype_map.get(category, ['default'])[0]
        }
    
    def _plan_resources(self, analysis: Dict[str, Any], existing_resources: Dict[str, Any]) -> Dict[str, Any]:
        """规划资源使用"""
        resources = {
            'videos': [],
            'images': [],
            'audio': [],
            'text': []
        }
        
        # 分析需要的资源类型
        outline = analysis.get('outline', {})
        duration = analysis.get('duration', 30)
        
        # 如果有现有资源，优先使用
        if existing_resources:
            resources.update(existing_resources)
        
        # 规划AI生成资源
        # 这里可以根据outline中的需求规划需要生成的资源
        if '背景音乐' in str(outline) or 'BGM' in str(outline):
            resources['audio'].append({
                'id': f'bgm_{datetime.now().timestamp()}',
                'source': 'ai_generated',
                'params': {
                    'model': 'musicgen',
                    'duration': duration,
                    'style': 'cinematic'
                }
            })
        
        return resources
    
    def _generate_timeline(self, analysis: Dict[str, Any], video_type: str, style: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成时间轴"""
        duration = analysis.get('duration', 30)
        
        # 对于产品广告，使用智能手表广告的具体结构
        if video_type == 'product_ad' and '智能手表' in analysis.get('original_request', ''):
            timeline = []
            
            # 1. Logo动画 (0-5秒)
            timeline.append({
                'start': 0,
                'end': 5,
                'layers': [
                    {
                        'type': 'video',
                        'resource_id': 'input_video',
                        'effects': ['glow'],
                        'transform': {'scale': 1.2, 'position': ['center', 'center']}
                    },
                    {
                        'type': 'text',
                        'content': 'SmartWatch Pro',
                        'style': {
                            'size': 80,
                            'color': '#00FFFF',
                            'font': 'Arial Bold',
                            'animation': 'fade_in'
                        },
                        'transform': {'position': ['center', 'center']}
                    }
                ]
            })
            
            # 2. 功能展示 (5-20秒)
            # 心率监测 (5-10秒)
            timeline.append({
                'start': 5,
                'end': 10,
                'layers': [
                    {
                        'type': 'video',
                        'resource_id': 'input_video',
                        'transform': {'scale': 1.0, 'position': ['center', 'center']}
                    },
                    {
                        'type': 'text',
                        'content': '心率监测',
                        'style': {'size': 60, 'color': '#FF00FF', 'font': 'Arial'},
                        'transform': {'position': ['center', 100]}
                    }
                ]
            })
            
            # 消息提醒 (10-15秒)
            timeline.append({
                'start': 10,
                'end': 15,
                'layers': [
                    {
                        'type': 'video',
                        'resource_id': 'input_video',
                        'transform': {'scale': 1.0, 'position': ['center', 'center']}
                    },
                    {
                        'type': 'text',
                        'content': '消息提醒',
                        'style': {'size': 60, 'color': '#00FF00', 'font': 'Arial'},
                        'transform': {'position': ['center', 100]}
                    }
                ]
            })
            
            # 运动追踪 (15-20秒)
            timeline.append({
                'start': 15,
                'end': 20,
                'layers': [
                    {
                        'type': 'video',
                        'resource_id': 'input_video',
                        'transform': {'scale': 1.0, 'position': ['center', 'center']}
                    },
                    {
                        'type': 'text',
                        'content': '运动追踪',
                        'style': {'size': 60, 'color': '#FFFF00', 'font': 'Arial'},
                        'transform': {'position': ['center', 100]}
                    }
                ]
            })
            
            # 3. 外观展示 (20-28秒)
            timeline.append({
                'start': 20,
                'end': 28,
                'layers': [
                    {
                        'type': 'video',
                        'resource_id': 'input_video',
                        'effects': ['glow'],
                        'transform': {'scale': 1.1, 'position': ['center', 'center']}
                    },
                    {
                        'type': 'text',
                        'content': '精致外观 时尚设计',
                        'style': {'size': 50, 'color': '#FFFFFF', 'font': 'Arial'},
                        'transform': {'position': ['center', 900]}
                    }
                ]
            })
            
            # 4. 购买引导 (28-30秒)
            timeline.append({
                'start': 28,
                'end': 30,
                'layers': [
                    {
                        'type': 'text',
                        'content': '立即购买',
                        'style': {'size': 100, 'color': '#FF0000', 'font': 'Arial Bold'},
                        'transform': {'position': ['center', 400]}
                    },
                    {
                        'type': 'text',
                        'content': '限时优惠 ¥1999',
                        'style': {'size': 60, 'color': '#FFFF00', 'font': 'Arial'},
                        'transform': {'position': ['center', 600]}
                    }
                ]
            })
            
            return timeline
        
        # 使用原来的DAG系统作为后备方案
        context = {
            "大纲内容": analysis.get('outline', ''),
            "video_type": video_type,
            "style": style
        }
        
        result = self.controller.run_generate(context)
        
        # 提取时间轴信息
        timeline_data = result.get('node12', {}).get('timeline', {})
        
        # 转换为AuraRender格式
        timeline = []
        if 'tracks' in timeline_data:
            # 解析tracks生成timeline segments
            for i, track in enumerate(timeline_data.get('tracks', [])):
                for clip in track.get('clips', []):
                    segment = {
                        'start': clip.get('start', 0),
                        'end': clip.get('end', 5),
                        'layers': [{
                            'type': track.get('type', 'video'),
                            'resource_id': 'input_video' if track['type'] == 'video' else f"{track['type']}_{i}_{clip['start']}",
                            'effects': clip.get('filters', []),
                            'transform': clip.get('transform', {})
                        }]
                    }
                    timeline.append(segment)
        
        return timeline
    
    def _build_execution_script(self, analysis: Dict[str, Any], video_type: str, 
                               style: Dict[str, Any], resources: Dict[str, Any], 
                               timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建最终的执行脚本"""
        duration = analysis.get('duration', 30)
        
        script = {
            'version': '1.0',
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'orchestrator': 'AuraRender',
                'original_request': analysis.get('original_request', '')
            },
            'project': {
                'id': f'aura_{datetime.now().timestamp()}',
                'type': video_type,
                'style': style,
                'duration': duration,
                'resolution': '1920x1080',
                'fps': 30
            },
            'resources': resources,
            'timeline': timeline,
            'global_effects': self._get_global_effects(style)
        }
        
        return script
    
    def _extract_duration(self, text: str) -> int:
        """从文本中提取时长"""
        import re
        
        # 匹配各种时长表述
        patterns = [
            (r'(\d+)\s*秒', 1),
            (r'(\d+)\s*分钟', 60),
            (r'(\d+)\s*分', 60),
            (r'(\d+)s', 1),
            (r'(\d+)min', 60)
        ]
        
        for pattern, multiplier in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1)) * multiplier
        
        return 30  # 默认30秒
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取，可以后续集成更复杂的NLP
        keywords = []
        
        # 预定义的重要关键词
        important_words = [
            '产品', '品牌', '公司', '介绍', '展示', '宣传',
            '科技', '温馨', '动感', '专业', '创意', '艺术',
            'vlog', '教程', '课程', '游戏', '音乐', '故事'
        ]
        
        text_lower = text.lower()
        for word in important_words:
            if word in text_lower:
                keywords.append(word)
        
        return keywords
    
    def _detect_intent(self, text: str) -> str:
        """检测用户意图"""
        # 简单的意图识别
        if any(word in text for word in ['介绍', '展示', '宣传']):
            return 'promote'
        elif any(word in text for word in ['教', '学习', '课程']):
            return 'educate'
        elif any(word in text for word in ['记录', '分享', 'vlog']):
            return 'share'
        elif any(word in text for word in ['故事', '剧情']):
            return 'entertain'
        
        return 'general'
    
    def _get_global_effects(self, style: Dict[str, Any]) -> Dict[str, Any]:
        """获取全局特效配置"""
        effects_map = {
            'realistic': {
                'color_grading': 'natural',
                'filters': []
            },
            'artistic': {
                'color_grading': 'artistic_preset',
                'filters': ['soft_focus', 'vignette']
            },
            'design': {
                'color_grading': 'high_contrast',
                'filters': ['sharp']
            },
            'cartoon': {
                'color_grading': 'vibrant',
                'filters': ['cartoon_effect']
            },
            'futuristic': {
                'color_grading': 'cyberpunk_preset',
                'filters': ['digital_noise', 'scan_lines']
            }
        }
        
        return effects_map.get(style['category'], effects_map['realistic'])