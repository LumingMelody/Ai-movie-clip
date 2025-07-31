"""
AuraRender 智能视频创作引擎

核心理念：分离智能决策和机械执行
- 智能编排层：负责理解用户需求，生成执行脚本
- 机械执行层：根据脚本精确执行视频渲染
"""

from .intelligent_layer.orchestrator import AuraOrchestrator
from .execution_layer.executor import AuraExecutor

__all__ = ['AuraOrchestrator', 'AuraExecutor']