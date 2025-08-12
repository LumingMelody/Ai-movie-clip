"""
统一的自然语言处理器
整合两套NL处理系统，提供统一接口
"""
import os
import json
import logging
from typing import Dict, Optional, Any, List
from pathlib import Path
from functools import lru_cache
import hashlib

# 导入两套处理器
from .natural_language_processor import VideoTimelineProcessor
from .core.nl_processor import NLProcessor


class UnifiedNLProcessor:
    """统一的自然语言处理器接口"""
    
    def __init__(self, use_ai: bool = True, cache_enabled: bool = True):
        """
        初始化统一处理器
        
        Args:
            use_ai: 是否使用AI处理（需要API key）
            cache_enabled: 是否启用缓存
        """
        self.logger = logging.getLogger(__name__)
        self.use_ai = use_ai
        self.cache_enabled = cache_enabled
        self.cache_dir = Path(".cache/nl_results")
        
        # 初始化本地处理器
        self.local_processor = VideoTimelineProcessor()
        
        # 尝试初始化AI处理器
        self.ai_processor = None
        if use_ai:
            try:
                self.ai_processor = NLProcessor()
                self.logger.info("AI处理器初始化成功")
            except Exception as e:
                self.logger.warning(f"AI处理器初始化失败: {e}，将使用本地处理器")
                self.use_ai = False
        
        if cache_enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def process(self, user_input: str, mode: str = "auto", duration: Optional[float] = None) -> Dict[str, Any]:
        """
        处理自然语言输入
        
        Args:
            user_input: 用户的自然语言描述
            mode: 处理模式 ("ai", "local", "auto")
                - ai: 强制使用AI处理
                - local: 强制使用本地处理
                - auto: 自动选择（优先AI，失败则降级到本地）
        
        Returns:
            时间轴JSON字典
        """
        # 检查缓存
        if self.cache_enabled:
            cached_result = self._get_cached_result(user_input)
            if cached_result:
                self.logger.info("使用缓存的处理结果")
                return cached_result
        
        result = None
        
        if mode == "ai" or (mode == "auto" and self.use_ai and self.ai_processor):
            result = self._process_with_ai(user_input, duration)
        
        if result is None and mode != "ai":
            result = self._process_with_local(user_input, duration)
        
        if result is None:
            raise Exception("无法处理输入，请检查配置")
        
        # 缓存结果
        if self.cache_enabled and result:
            self._cache_result(user_input, result)
        
        return result
    
    def _process_with_ai(self, user_input: str, duration: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """使用AI处理器处理"""
        try:
            self.logger.info("使用AI处理器处理自然语言...")
            
            # 获取AI生成的大纲
            outline = self.ai_processor.process_natural_language(user_input)
            
            # 提取关键元素
            elements = self.ai_processor.extract_key_elements(outline)
            
            # 使用本地处理器生成详细时间轴
            # 结合AI的理解和本地的结构化处理
            enhanced_input = self._enhance_input_with_ai_elements(user_input, elements, outline)
            timeline = self.local_processor.generate_timeline_from_text(enhanced_input, duration)
            
            # 添加AI生成的元数据
            timeline["metadata"] = timeline.get("metadata", {})
            timeline["metadata"]["ai_outline"] = outline
            timeline["metadata"]["ai_elements"] = elements
            timeline["metadata"]["processor"] = "ai"
            
            return timeline
            
        except Exception as e:
            self.logger.error(f"AI处理失败: {e}")
            return None
    
    def _process_with_local(self, user_input: str, duration: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """使用本地处理器处理"""
        try:
            self.logger.info("使用本地处理器处理自然语言...")
            
            timeline = self.local_processor.generate_timeline_from_text(user_input, duration)
            
            # 添加元数据
            timeline["metadata"] = timeline.get("metadata", {})
            timeline["metadata"]["processor"] = "local"
            
            return timeline
            
        except Exception as e:
            self.logger.error(f"本地处理失败: {e}")
            return None
    
    def _enhance_input_with_ai_elements(self, original_input: str, elements: Dict, outline: str) -> str:
        """
        使用AI提取的元素增强原始输入
        
        Args:
            original_input: 原始用户输入
            elements: AI提取的关键元素
            outline: AI生成的大纲
        
        Returns:
            增强后的输入文本
        """
        enhanced_parts = [original_input]
        
        # 添加时长信息
        if elements.get("duration"):
            duration_text = elements["duration"]
            if duration_text not in original_input:
                enhanced_parts.append(f"时长{duration_text}")
        
        # 添加风格信息
        if elements.get("style"):
            style_text = elements["style"]
            if style_text not in original_input:
                enhanced_parts.append(f"风格{style_text}")
        
        # 添加特效信息
        if elements.get("effects"):
            effects = elements["effects"]
            if isinstance(effects, list) and effects:
                effects_text = "、".join(effects)
                enhanced_parts.append(f"包含{effects_text}特效")
        
        # 从大纲中提取额外信息
        if "背景音乐" in outline and "背景音乐" not in original_input:
            enhanced_parts.append("配背景音乐")
        
        if "字幕" in outline and "字幕" not in original_input:
            enhanced_parts.append("添加字幕")
        
        return "，".join(enhanced_parts)
    
    def _get_cache_key(self, user_input: str) -> str:
        """生成缓存键"""
        return hashlib.md5(user_input.encode()).hexdigest()
    
    def _get_cached_result(self, user_input: str) -> Optional[Dict[str, Any]]:
        """获取缓存结果"""
        if not self.cache_enabled:
            return None
        
        cache_key = self._get_cache_key(user_input)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"读取缓存失败: {e}")
        
        return None
    
    def _cache_result(self, user_input: str, result: Dict[str, Any]):
        """缓存处理结果"""
        if not self.cache_enabled:
            return
        
        cache_key = self._get_cache_key(user_input)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"结果已缓存: {cache_key}")
        except Exception as e:
            self.logger.warning(f"缓存结果失败: {e}")
    
    def clear_cache(self):
        """清除所有缓存"""
        if self.cache_dir.exists():
            import shutil
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info("缓存已清除")
    
    def get_processor_status(self) -> Dict[str, Any]:
        """获取处理器状态"""
        return {
            "ai_available": self.ai_processor is not None,
            "cache_enabled": self.cache_enabled,
            "cache_size": len(list(self.cache_dir.glob("*.json"))) if self.cache_dir.exists() else 0,
            "default_mode": "ai" if self.use_ai and self.ai_processor else "local"
        }


class NaturalLanguageProcessor:
    """向后兼容的处理器类"""
    
    def __init__(self):
        """初始化处理器"""
        self.processor = UnifiedNLProcessor(use_ai=True, cache_enabled=True)
    
    def process_natural_language(self, user_input: str) -> Dict[str, Any]:
        """
        处理自然语言输入（向后兼容接口）
        
        Args:
            user_input: 用户的自然语言描述
            
        Returns:
            时间轴JSON字典
        """
        return self.processor.process(user_input, mode="auto")