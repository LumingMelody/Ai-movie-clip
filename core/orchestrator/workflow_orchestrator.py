# orchestrator/workflow_orchestrator.py - 重构版本
# -*- coding: utf-8 -*-
"""
视频剪辑工作流程编排器 - 重构版本
功能：协调视频分析、AI策略生成和视频剪辑的完整流程
"""

import json
import os
import time
from typing import Dict, Any, List, Optional

from moviepy import VideoFileClip, concatenate_videoclips

from core.ai.ai_model_caller import AIModelCaller
from core.utils.config_manager import config, ErrorHandler, PathHelper
from core.utils.video_utils import video_processor

# 设置Python路径
config.setup_python_path()

print(f"当前工作目录: {os.getcwd()}")
print(f"项目路径信息: {config.get_project_paths()}")


class VideoEditingOrchestrator:
    """视频剪辑工作流程编排器 - 重构版本"""

    def __init__(self, video_files: List[str], output_dir: str = None, analysis_results: List[Dict] = None):
        self.video_files = video_files
        self.output_dir = output_dir or config.video_config['default_output_dir']
        self.analysis_results = analysis_results or []
        self.editing_strategies = []
        self.start_time = None
        self.video_config = config.get_config('video')
        self.output_config = config.get_config('output')

        # 导入转场和特效模块
        self._import_effects_modules()

    def _import_effects_modules(self):
        """导入转场和特效模块"""
        try:
            from core.clipeffects.easy_clip_effects import vignette
            self.effects = {'vignette': vignette}
            ErrorHandler.log_success("成功导入特效模块")
        except ImportError as e:
            ErrorHandler.handle_import_error("特效模块", e, "使用基础功能")
            self.effects = {}

    def run_complete_workflow(self, user_options: Dict[str, Any] = None, api_key: str = None,
                              use_local_ai: bool = False, merge_videos: bool = True):
        """运行完整的剪辑工作流程"""
        workflow_steps = [
            ("视频识别与预处理", self._step1_video_identification),
            ("内容分析与分类", self._step2_content_analysis_wrapper),
            ("剪辑策略生成", lambda: self._step3_generate_editing_strategy(user_options, api_key, use_local_ai)),
            ("执行剪辑操作", self._step4_execute_editing),
            ("输出最终视频", lambda edited_clips: self._step5_output_final_video(edited_clips, merge_videos))
        ]
        
        return self._execute_workflow_steps(workflow_steps)
    
    def _execute_workflow_steps(self, steps: List[tuple]) -> Dict[str, Any]:
        """执行工作流程步骤"""
        self.start_time = time.time()
        print("🚀 开始AI视频自动剪辑流程...")
        
        try:
            results = {}
            
            # 执行前4个步骤
            for i, (step_name, step_func) in enumerate(steps[:-1]):
                print(f"\n📋 步骤{i+1}: {step_name}")
                if i == 0:
                    results['processed_videos'] = step_func()
                elif i == 1:
                    step_func()  # 分析步骤
                elif i == 2:
                    step_func()  # 策略生成步骤
                elif i == 3:
                    results['edited_clips'] = step_func()
            
            # 验证剪辑结果
            edited_clips = [clip for clip in results['edited_clips'] if clip is not None]
            if not edited_clips:
                raise ValueError("所有剪辑内容均为None，无法生成视频")
            
            # 执行最后步骤（输出）
            final_step_name, final_step_func = steps[-1]
            print(f"\n📋 步骤5: {final_step_name}")
            final_result = final_step_func(edited_clips)
            
            # 添加处理时间
            processing_time = time.time() - self.start_time
            final_result["processing_time"] = round(processing_time, 2)
            
            return final_result
            
        except Exception as e:
            return self._handle_workflow_error(e)

    def _step1_video_identification(self):
        """步骤1: 视频数量识别与预处理"""
        video_count = len(self.video_files)
        if video_count == 1:
            print(f"  单个视频: {os.path.basename(self.video_files[0])}")
        else:
            print(f"  多个视频: {video_count}个文件")
        return self.video_files
    
    def _step2_content_analysis_wrapper(self):
        """步骤2包装器: 内容分析与分类"""
        if not self.analysis_results:
            print("\n🔍 没有提供分析结果，开始重新分析...")
            self._step2_content_analysis()
        else:
            print(f"\n✅ 使用现有分析结果 ({len(self.analysis_results)} 个视频)")
            self._print_existing_analysis()
    
    def _handle_workflow_error(self, error: Exception) -> Dict[str, Any]:
        """处理工作流程错误"""
        ErrorHandler.handle_api_error("工作流程", error)
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        return {
            "status": "failed",
            "error": str(error),
            "processing_time": time.time() - self.start_time if self.start_time else 0
        }

    def _print_existing_analysis(self):
        """打印现有分析结果的摘要"""
        for i, analysis in enumerate(self.analysis_results):
            video_name = os.path.basename(analysis.get('file_path', f'视频{i + 1}'))
            classification = analysis.get('classification', {})
            metadata = analysis.get('metadata', {})

            print(f"  📹 {video_name}")
            print(f"    时长: {metadata.get('duration', 0):.1f}秒")
            print(f"    内容类型: {classification.get('content_type', '未知')}")

    def _step2_content_analysis(self):
        """步骤2: 内容分析与分类判断"""
        analyzer = self._import_video_analyzer()
        
        for video_path in self.video_files:
            print(f"  分析视频: {os.path.basename(video_path)}")
            analysis_result = analyzer.analyze_video(video_path)
            self.analysis_results.append(analysis_result)
            
            classification = analysis_result.get('classification', {})
            print(f"    内容类型: {classification.get('content_type', '未知')}")
    
    def _import_video_analyzer(self):
        """导入视频分析器"""
        import_attempts = [
            ('analyzer.video_analyzer', lambda: __import__('analyzer.video_analyzer', fromlist=['VideoAnalyzer']).VideoAnalyzer()),
            ('core.analyzer.video_analyzer', lambda: __import__('core.analyzer.video_analyzer', fromlist=['VideoAnalyzer']).VideoAnalyzer()),
        ]
        
        for import_path, import_func in import_attempts:
            try:
                print(f"    尝试导入: {import_path}")
                analyzer = import_func()
                ErrorHandler.log_success(f"成功导入: {import_path}")
                return analyzer
            except ImportError as e:
                ErrorHandler.handle_import_error(import_path, e)
                continue
        
        raise ImportError("无法找到 VideoAnalyzer")

    def _step3_generate_editing_strategy(self, user_options: Dict[str, Any], api_key: str, use_local_ai: bool):
        """步骤3: 策略生成"""
        user_options = self._prepare_user_options(user_options)
        
        for i, analysis in enumerate(self.analysis_results):
            print(f"  为视频 {i + 1} 生成策略...")
            strategy = self._generate_single_strategy(analysis, user_options, api_key, use_local_ai)
            self.editing_strategies.append(strategy)
            
            actions = strategy.get('actions', [])
            print(f"    📊 策略生成完成，包含 {len(actions)} 个操作")
    
    def _prepare_user_options(self, user_options: Dict[str, Any]) -> Dict[str, Any]:
        """准备用户选项"""
        default_options = {
            "target_duration": self.video_config['default_target_duration'],
            "target_style": "抖音风",
            "target_purpose": "社交媒体"
        }
        return {**default_options, **(user_options or {})}
    
    def _generate_single_strategy(self, analysis: Dict[str, Any], user_options: Dict[str, Any], 
                                api_key: str, use_local_ai: bool) -> Dict[str, Any]:
        """为单个视频生成策略"""
        if use_local_ai or not api_key:
            if not api_key:
                ErrorHandler.log_warning("未提供API key，使用本地策略")
            return self._generate_local_strategy(analysis, user_options)
        
        print(f"    🤖 使用AI策略生成")
        return self._generate_ai_multi_segment_strategy(analysis, user_options, api_key)
    
    def _generate_local_strategy(self, analysis: Dict[str, Any], user_options: Dict[str, Any]) -> Dict[str, Any]:
        """生成本地策略"""
        # 简化的本地策略生成逻辑
        target_duration = user_options.get('target_duration', 30)
        return {
            "target_duration": target_duration,
            "strategy_type": "single_segment",
            "actions": [{
                "function": "cut",
                "start": 0,
                "end": target_duration,
                "reason": "本地策略简单剪辑"
            }],
            "metadata": {
                "source": "local",
                "confidence": 0.6
            }
        }

    def _generate_ai_multi_segment_strategy(self, analysis: Dict[str, Any], user_options: Dict[str, Any],
                                            api_key: str) -> Dict[str, Any]:
        """使用AI生成策略"""
        try:
            prompt = self._build_enhanced_prompt(analysis, user_options)
            ai_caller = AIModelCaller(api_key=api_key)
            strategy = ai_caller.generate_editing_plan(prompt, use_local=False)

            if strategy.get('strategy_type') in ['multi_segment', 'single_segment']:
                print("    ✅ AI策略生成成功")
                return strategy
            else:
                print("    ❌ AI策略格式不符，生成失败")
                raise Exception("AI策略格式无效")

        except Exception as e:
            print(f"    ❌ AI策略生成失败: {e}")
            raise Exception(f"AI策略生成失败: {e}")

    def _build_enhanced_prompt(self, analysis: Dict[str, Any], user_options: Dict[str, Any]) -> str:
        """构建AI提示词"""
        metadata = analysis.get('metadata', {})
        classification = analysis.get('classification', {})

        simplified_input = {
            "metadata": {
                "duration": metadata.get('duration', 0),
                "content_type": classification.get('content_type', ''),
                "has_audio": metadata.get('has_audio', True)
            }
        }

        user_requirements = {
            "target_duration": user_options.get('target_duration', 30),
            "target_style": user_options.get('target_style', '抖音风'),
            "target_purpose": user_options.get('target_purpose', '社交媒体')
        }

        prompt = f"""请为以下视频生成剪辑策略：

视频信息：
时长: {simplified_input['metadata']['duration']:.1f}秒
内容类型: {simplified_input['metadata']['content_type']}

用户需求：
目标时长: {user_requirements['target_duration']}秒
风格: {user_requirements['target_style']}
用途: {user_requirements['target_purpose']}

请生成剪辑策略。"""

        return prompt

    def _step4_execute_editing(self):
        """步骤4: 执行剪辑操作"""
        edited_clips = []
        
        for i, (video_path, strategy) in enumerate(zip(self.video_files, self.editing_strategies)):
            print(f"  剪辑视频 {i + 1}: {os.path.basename(video_path)}")
            
            try:
                final_clip = self._safe_video_editing(video_path, strategy)
                edited_clips.append(final_clip)
                print(f"    ✅ 完成剪辑，最终时长: {final_clip.duration:.1f}秒")
            except Exception as e:
                ErrorHandler.handle_file_error("剪辑", video_path, e)
                # 可以选择继续或抛出异常
                raise
        
        return edited_clips

    def _safe_video_editing(self, video_path: str, strategy: Dict[str, Any]):
        """安全的视频剪辑方法"""
        print(f"    📥 安全加载视频: {os.path.basename(video_path)}")
        
        # 使用统一的视频处理器加载视频
        clip, has_audio = video_processor.safe_load_video(video_path)
        if clip is None:
            raise ValueError(f"无法加载视频: {video_path}")
        
        try:
            actions = strategy.get('actions', [])
            strategy_type = strategy.get('strategy_type', 'single_segment')
            
            print(f"    📋 策略类型: {strategy_type}")
            print(f"    📋 操作数量: {len(actions)}")
            
            # 根据策略类型处理
            if strategy_type == 'multi_segment':
                return self._execute_multi_segment_strategy_safe(clip, actions, has_audio)
            else:
                return self._execute_single_segment_strategy(clip, actions, has_audio)
        
        except Exception as e:
            clip.close()
            raise e

    def _execute_single_segment_strategy(self, clip, actions, has_audio):
        """执行单片段策略 - 完全安全版本"""
        print(f"    ✂️ 执行单片段策略")

        # 查找cut操作
        cut_actions = [a for a in actions if a.get('function') == 'cut']

        if not cut_actions:
            print(f"    ⚠️ 没有找到cut操作，使用原视频")
            return clip

        # 执行第一个cut操作
        action = cut_actions[0]
        start = action.get('start', 0)
        end = action.get('end', clip.duration)

        # 确保时间范围有效
        start = max(0, start)
        end = min(end, clip.duration)

        print(f"    🔧 执行剪辑: {start:.1f}s - {end:.1f}s (时长: {end - start:.1f}s)")

        if start < end and (end - start) > 0.5:
            try:
                # 🔥 关键修复3: 先处理视频，再安全处理音频
                if has_audio:
                    try:
                        # 方法1: 尝试同时剪辑视频和音频
                        clipped = clip.subclipped(start, end)

                        # 🔥 关键修复4: 验证音频剪辑是否成功
                        if clipped.audio is not None:
                            try:
                                # 测试音频是否可用
                                _ = clipped.audio.duration
                                print(f"    ✅ 单片段剪辑成功 (含音频): {clipped.duration:.1f}s")
                                return clipped
                            except Exception as audio_error:
                                print(f"    ⚠️ 音频剪辑后不可用，移除音频: {audio_error}")
                                clipped = clipped.without_audio()

                        print(f"    ✅ 单片段剪辑成功 (无音频): {clipped.duration:.1f}s")
                        return clipped

                    except Exception as e:
                        print(f"    ⚠️ 含音频剪辑失败，尝试无音频剪辑: {e}")
                        # 方法2: 如果音频剪辑失败，先移除音频再剪辑
                        video_only = clip.without_audio()
                        clipped = video_only.subclipped(start, end)
                        print(f"    ✅ 单片段剪辑成功 (无音频备用方案): {clipped.duration:.1f}s")
                        return clipped
                else:
                    # 无音频，直接剪辑
                    clipped = clip.subclipped(start, end)
                    print(f"    ✅ 单片段剪辑成功 (无音频): {clipped.duration:.1f}s")
                    return clipped

            except Exception as e:
                print(f"    ❌ 剪辑操作失败: {e}")
                print(f"    🔄 使用原视频作为备用方案")
                return clip.without_audio() if has_audio else clip
        else:
            print(f"    ⚠️ 剪辑范围无效，使用原视频")
            return clip.without_audio() if has_audio else clip

    def _execute_multi_segment_strategy_safe(self, clip, actions, has_audio):
        """执行多片段策略 - 完全安全版本"""
        print(f"    🎬 执行多片段策略")

        # 提取所有extract_segment操作
        extract_actions = [a for a in actions if a.get('action') == 'extract_segment']

        if not extract_actions:
            print(f"    ⚠️ 没有找到extract_segment操作，使用原视频")
            return clip.without_audio() if has_audio else clip

        print(f"    🔪 找到 {len(extract_actions)} 个片段要提取:")

        segment_clips = []

        try:
            for i, action in enumerate(extract_actions):
                start = action.get('start', 0)
                end = action.get('end', clip.duration)
                reason = action.get('reason', f'片段{i + 1}')

                # 确保时间范围有效
                start = max(0, start)
                end = min(end, clip.duration)

                print(f"      {i + 1}. 提取 {start:.1f}s - {end:.1f}s ({end - start:.1f}s) - {reason}")

                if start < end and (end - start) > 0.5:
                    try:
                        # 🔥 关键修复5: 对多片段也应用安全的音频处理
                        if has_audio:
                            try:
                                subclipped = clip.subclipped(start, end)
                                # 验证音频
                                if subclipped.audio is not None:
                                    _ = subclipped.audio.duration
                                segment_clips.append(subclipped)
                                print(f"        ✅ 片段{i + 1}提取成功 (含音频): {subclipped.duration:.1f}s")
                            except Exception as audio_error:
                                print(f"        ⚠️ 片段{i + 1}音频处理失败，使用无音频版本: {audio_error}")
                                subclipped = clip.without_audio().subclipped(start, end)
                                segment_clips.append(subclipped)
                                print(f"        ✅ 片段{i + 1}提取成功 (无音频): {subclipped.duration:.1f}s")
                        else:
                            subclipped = clip.subclipped(start, end)
                            segment_clips.append(subclipped)
                            print(f"        ✅ 片段{i + 1}提取成功: {subclipped.duration:.1f}s")

                    except Exception as e:
                        print(f"        ❌ 片段{i + 1}提取失败: {e}")
                else:
                    print(f"        ⚠️ 跳过无效片段{i + 1}: 时长{end - start:.1f}s")

            if not segment_clips:
                print(f"    ❌ 没有成功提取任何片段，使用原视频")
                return clip.without_audio() if has_audio else clip

            # 合并片段 - 使用chain方法确保兼容性
            print(f"    🔗 合并 {len(segment_clips)} 个片段...")
            combined_clip = concatenate_videoclips(segment_clips, method="chain")
            print(f"    ✅ 多片段合并成功: {combined_clip.duration:.1f}s")

            return combined_clip

        except Exception as e:
            print(f"    ❌ 多片段处理失败: {e}")
            return clip.without_audio() if has_audio else clip

    def _step5_output_final_video(self, edited_clips, merge_videos: bool):
        """步骤5: 输出最终视频"""
        PathHelper.ensure_dir_exists(self.output_dir)
        output_filename = "edited_video.mp4"
        output_path = os.path.join(self.output_dir, output_filename)

        # 更安全的合并方式
        valid_clips = [clip for clip in edited_clips if clip is not None]
        if not valid_clips:
            raise ValueError("没有有效的剪辑内容")

        # 🔥 关键修复: 多视频合并前统一视频格式，防止撕裂
        if len(valid_clips) == 1:
            final_clip = valid_clips[0]
        else:
            print(f"  🔧 统一 {len(valid_clips)} 个视频的格式参数...")
            
            # 获取所有视频的格式信息
            clip_info = []
            for i, clip in enumerate(valid_clips):
                info = {
                    'clip': clip,
                    'w': clip.w,
                    'h': clip.h,
                    'fps': clip.fps or 24,
                    'duration': clip.duration
                }
                clip_info.append(info)
                print(f"    视频{i+1}: {info['w']}x{info['h']} @{info['fps']}fps, {info['duration']:.1f}s")
            
            # 计算统一的目标格式（使用最小公约数确保兼容性）
            target_w = min(info['w'] for info in clip_info)
            target_h = min(info['h'] for info in clip_info)
            target_fps = 24  # 统一使用24fps
            
            # 确保分辨率是偶数（视频编码要求）
            target_w = target_w - (target_w % 2)
            target_h = target_h - (target_h % 2)
            
            print(f"    🎯 目标格式: {target_w}x{target_h} @{target_fps}fps")
            
            # 标准化所有视频片段
            standardized_clips = []
            for i, info in enumerate(clip_info):
                clip = info['clip']
                try:
                    # 统一分辨率和帧率
                    if (clip.w != target_w or clip.h != target_h or clip.fps != target_fps):
                        print(f"    🔄 标准化视频{i+1}: {clip.w}x{clip.h}@{clip.fps}fps -> {target_w}x{target_h}@{target_fps}fps")
                        standardized_clip = clip.resized((target_w, target_h)).with_fps(target_fps)
                    else:
                        standardized_clip = clip
                        print(f"    ✅ 视频{i+1}格式已符合要求")
                    
                    standardized_clips.append(standardized_clip)
                    
                except Exception as e:
                    print(f"    ⚠️ 视频{i+1}标准化失败，使用原视频: {e}")
                    standardized_clips.append(clip)
            
            # 使用chain方法合并，避免格式冲突
            print(f"    🔗 合并标准化后的视频片段...")
            final_clip = concatenate_videoclips(standardized_clips, method="chain")

        print(f"  📊 输出前检查:")
        print(f"    - 时长: {final_clip.duration:.1f}秒")
        print(f"    - 分辨率: {final_clip.w}x{final_clip.h}")
        print(f"    - FPS: {final_clip.fps}")
        print(f"    - 音频: {'有' if final_clip.audio else '无'}")

        # 🔥 关键修复6: 彻底修复输出参数和音频处理
        try:
            print("  🔄 开始安全输出...")

            # 确保基本属性
            if not hasattr(final_clip, 'fps') or final_clip.fps is None:
                final_clip.fps = 24

            # 🔥 关键修复7: 优化输出参数，避免音频问题
            write_params = {
                "fps": final_clip.fps,
                "codec": "libx264",
                "preset": "medium",  # 改为medium提高兼容性
                "threads": 1,  # 使用单线程避免死锁
                "logger": None,
                "temp_audiofile": 'temp-audio.m4a',  # 指定临时音频文件
                "remove_temp": True  # 自动清理临时文件
            }

            # 🔥 关键修复8: 更安全的音频处理
            if final_clip.audio is not None:
                try:
                    # 验证音频可用性
                    _ = final_clip.audio.duration
                    write_params["audio_codec"] = "aac"
                    write_params["audio_bitrate"] = "128k"
                    print("  🎵 音频输出已启用")
                except Exception as audio_error:
                    print(f"  ⚠️ 音频输出失败，移除音频: {audio_error}")
                    final_clip = final_clip.without_audio()
                    print("  🔇 改为无音频输出")

            # 执行输出
            final_clip.write_videofile(output_path, **write_params)
            print("  ✅ 视频输出成功！")

            # 验证输出
            if os.path.exists(output_path):
                file_size = round(os.path.getsize(output_path) / (1024 * 1024), 2)
                print(f"\n  📁 完全修复版输出验证:")
                print(f"    - 文件: {output_path}")
                print(f"    - 大小: {file_size}MB")

                result = {
                    "status": "success",
                    "output_video": output_path,
                    "file_size_mb": file_size,
                    "video_info": {
                        "duration": final_clip.duration,
                        "resolution": f"{final_clip.w}x{final_clip.h}",
                        "fps": final_clip.fps,
                        "has_audio": final_clip.audio is not None
                    }
                }
                return result
            else:
                raise Exception("输出文件未成功生成")

        except Exception as e:
            print(f"  ❌ 输出失败: {e}")
            raise e

        finally:
            # 确保资源释放
            try:
                final_clip.close()
            except:
                pass
            for clip in edited_clips:
                try:
                    if clip:
                        clip.close()
                except:
                    pass

    def cleanup(self):
        """清理资源"""
        pass


# 从分析结果创建工作流程的便捷函数
def create_orchestrator_from_analysis(analysis_file: str, output_dir: str = None):
    """从分析结果文件创建工作流程编排器"""

    with open(analysis_file, 'r', encoding='utf-8') as f:
        analysis_results = json.load(f)

    video_files = []
    for result in analysis_results:
        path = result.get('file_path') or result.get('filepath') or result.get('metadata', {}).get('filepath')
        if path and os.path.exists(path):
            video_files.append(path)

    if not video_files:
        raise ValueError("分析结果中没有找到有效的视频文件路径")

    print(f"从分析结果中找到 {len(video_files)} 个视频文件")

    return VideoEditingOrchestrator(
        video_files=video_files,
        output_dir=output_dir,
        analysis_results=analysis_results
    )
