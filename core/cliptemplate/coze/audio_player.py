"""
跨平台音频播放器模块
提供稳定的音频播放功能，支持 Windows、macOS 和 Linux
"""

import os
import platform
import subprocess
import time
import threading


class AudioPlayer:
    """跨平台音频播放器"""
    
    @staticmethod
    def play(audio_file, block=False):
        """
        播放音频文件
        
        Args:
            audio_file: 音频文件路径
            block: 是否阻塞等待播放完成
        
        Returns:
            bool: 播放是否成功启动
        """
        if not os.path.exists(audio_file):
            print(f"❌ 音频文件不存在: {audio_file}")
            return False
            
        system = platform.system()
        abs_path = os.path.abspath(audio_file)
        
        try:
            if system == 'Windows':
                return AudioPlayer._play_windows(abs_path, block)
            elif system == 'Darwin':  # macOS
                return AudioPlayer._play_macos(abs_path, block)
            elif system == 'Linux':
                return AudioPlayer._play_linux(abs_path, block)
            else:
                print(f"⚠️ 不支持的操作系统: {system}")
                return False
        except Exception as e:
            print(f"⚠️ 播放音频时出错: {e}")
            return False
    
    @staticmethod
    def _play_windows(audio_file, block):
        """Windows 平台播放音频"""
        # 验证文件格式和大小
        try:
            file_size = os.path.getsize(audio_file)
            print(f"📁 音频文件信息: {os.path.basename(audio_file)}, 大小: {file_size} 字节")
            
            if file_size == 0:
                print(f"❌ 音频文件为空，无法播放")
                return False
        except Exception as e:
            print(f"❌ 无法读取音频文件信息: {e}")
            return False
        
        # 方法1: 使用 Windows Media Player COM 对象
        try:
            import win32com.client
            import pythoncom
            
            print(f"🔊 尝试Windows COM音频播放: {audio_file}")
            
            # 初始化COM
            pythoncom.CoInitialize()
            try:
                wmp = win32com.client.Dispatch("WMPlayer.OCX")
                
                # 检查播放器版本和能力
                try:
                    version = wmp.versionInfo
                    print(f"🎮 Windows Media Player版本: {version}")
                except:
                    print(f"🎮 Windows Media Player版本: 未知")
                
                # 设置音量和静音状态
                wmp.settings.volume = 100
                wmp.settings.mute = False
                print(f"🔊 音量设置: {wmp.settings.volume}, 静音: {wmp.settings.mute}")
                
                # 先停止任何正在播放的内容
                try:
                    wmp.controls.stop()
                    time.sleep(0.2)
                except:
                    pass
                
                # 加载音频文件
                print(f"📂 正在加载音频文件...")
                wmp.URL = audio_file
                
                # 等待文件加载
                load_timeout = 5
                load_waited = 0
                while load_waited < load_timeout:
                    try:
                        if wmp.currentMedia and wmp.currentMedia.duration > 0:
                            print(f"✅ 文件加载成功，时长: {wmp.currentMedia.duration}秒")
                            break
                    except:
                        pass
                    time.sleep(0.2)
                    load_waited += 0.2
                
                if load_waited >= load_timeout:
                    print(f"⚠️ 文件加载超时，尝试直接播放")
                
                # 开始播放
                print(f"▶️ 开始播放...")
                wmp.controls.play()
                
                # 短暂等待播放开始
                time.sleep(1.0)
                
                # 状态码映射
                state_names = {
                    0: "未定义", 1: "停止", 2: "暂停", 3: "播放", 
                    4: "扫描前进", 5: "扫描后退", 6: "缓冲", 
                    7: "等待", 8: "准备就绪", 9: "重连/错误", 10: "就绪"
                }
                
                current_state = wmp.playState
                state_name = state_names.get(current_state, f"未知({current_state})")
                print(f"🎵 当前播放状态: {current_state} ({state_name})")
                
                # 如果是错误状态，尝试其他方法
                if current_state == 9:
                    print(f"⚠️ COM播放器遇到错误，尝试其他播放方法")
                    raise Exception("COM播放器状态错误")
                
                # 检查是否真的在播放
                if current_state in [3, 6, 7, 8]:  # 播放、缓冲、等待、准备就绪
                    print(f"✅ Windows COM播放启动成功")
                    
                    if block:
                        # 等待播放完成
                        max_wait = 30  # 最多等待30秒
                        waited = 0
                        last_state = current_state
                        retry_count = 0
                        
                        while wmp.playState not in [1, 0] and waited < max_wait:
                            time.sleep(0.3)
                            waited += 0.3
                            
                            current_state = wmp.playState
                            if current_state != last_state:
                                state_name = state_names.get(current_state, f"未知({current_state})")
                                print(f"🔄 播放状态变化: {last_state} → {current_state} ({state_name})")
                                last_state = current_state
                            
                            # 每3秒打印一次状态
                            if int(waited) % 3 == 0 and waited - int(waited) < 0.3:
                                state_name = state_names.get(current_state, f"未知({current_state})")
                                print(f"📊 播放状态: {current_state} ({state_name}), 已播放: {waited:.1f}s")
                            
                            # 如果状态是错误且重试次数少于2次
                            if current_state == 9 and retry_count < 2:
                                print(f"⚠️ 检测到错误状态，尝试重新播放 (第{retry_count + 1}次)")
                                wmp.controls.stop()
                                time.sleep(0.5)
                                wmp.controls.play()
                                time.sleep(1.0)
                                retry_count += 1
                                waited = 0  # 重置等待时间
                        
                        if waited >= max_wait:
                            print(f"⏰ 播放超时，强制结束")
                            wmp.controls.stop()
                        else:
                            print(f"✅ Windows COM播放完成")
                    
                    return True
                else:
                    print(f"❌ COM播放器未能正常启动播放")
                    raise Exception(f"播放器状态异常: {current_state}")
                    
            finally:
                # 清理COM
                try:
                    pythoncom.CoUninitialize()
                except:
                    pass
                
        except (ImportError, Exception) as e:
            print(f"❌ Windows COM播放失败: {e}")
            # 继续尝试其他方法
            pass
        
        try:
            # 方法2: 使用 pygame
            import pygame
            
            print(f"🔊 尝试pygame音频播放: {audio_file}")
            
            # 先停止现有播放
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()
                    time.sleep(0.2)
            except:
                pass
            
            # 重新初始化pygame mixer，使用更好的设置
            try:
                pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
                pygame.mixer.init()
                print(f"🎮 pygame mixer初始化成功: {pygame.mixer.get_init()}")
            except Exception as init_e:
                print(f"⚠️ pygame初始化警告: {init_e}")
                # 尝试简单初始化
                pygame.mixer.init()
            
            # 设置音量
            pygame.mixer.music.set_volume(1.0)  # 最大音量
            
            # 加载和播放
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            
            # 检查播放状态
            time.sleep(0.5)
            if pygame.mixer.music.get_busy():
                print(f"✅ pygame播放启动成功")
                
                if block:
                    max_wait = 30  # 最多等待30秒
                    waited = 0
                    last_check = 0
                    
                    while pygame.mixer.music.get_busy() and waited < max_wait:
                        pygame.time.Clock().tick(10)
                        waited += 0.1
                        
                        # 每2秒打印一次状态
                        if waited - last_check >= 2.0:
                            print(f"📊 pygame播放中，已播放: {waited:.1f}s")
                            last_check = waited
                    
                    if waited >= max_wait:
                        print(f"⏰ pygame播放超时，强制停止")
                        pygame.mixer.music.stop()
                    else:
                        print(f"✅ pygame播放完成")
                
                return True
            else:
                print(f"❌ pygame播放未能正常启动")
                raise Exception("pygame播放器未能正常启动")
                
        except (ImportError, Exception) as e:
            print(f"❌ pygame音频播放失败: {e}")
            pass
        
        try:
            # 方法3: 使用 Windows 内置命令播放MP3/WAV
            print(f"🔊 尝试Windows PowerShell播放: {audio_file}")
            
            if audio_file.lower().endswith('.wav'):
                # WAV文件使用SoundPlayer
                cmd = [
                    'powershell', '-c',
                    f'(New-Object Media.SoundPlayer "{audio_file}").PlaySync()'
                ]
            else:
                # MP3文件使用Windows Media Player
                cmd = [
                    'powershell', '-c',
                    f'Add-Type -AssemblyName presentationCore; $player = New-Object System.Windows.Media.MediaPlayer; $player.Open([uri]"{audio_file}"); $player.Play(); Start-Sleep -Seconds 5'
                ]
            
            if block:
                result = subprocess.run(cmd, shell=False, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ PowerShell播放成功")
                    return True
                else:
                    print(f"❌ PowerShell播放失败: {result.stderr}")
            else:
                subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"✅ PowerShell播放启动成功")
                return True
        except Exception as e:
            print(f"❌ PowerShell音频播放失败: {e}")
            pass
        
        # 方法4: 使用Windows系统命令直接播放
        try:
            print(f"🔊 尝试Windows start命令播放: {audio_file}")
            
            # 使用Windows start命令用默认程序播放
            if block:
                # 同步模式：等待播放器关闭
                result = subprocess.run(['start', '/wait', '""', f'"{audio_file}"'], 
                                      shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ Windows start命令播放成功")
                    return True
                else:
                    print(f"⚠️ start命令返回码: {result.returncode}")
            else:
                # 异步模式：立即返回
                subprocess.Popen(['start', '""', f'"{audio_file}"'], shell=True)
                print(f"✅ Windows start命令启动成功")
                return True
        except Exception as e:
            print(f"❌ Windows start命令失败: {e}")
        
        # 方法5: 使用mplay32.exe
        try:
            print(f"🔊 尝试mplay32播放: {audio_file}")
            
            result = subprocess.run(['mplay32', '/play', '/close', audio_file], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ mplay32播放成功")
                return True
            else:
                print(f"❌ mplay32播放失败: {result.stderr}")
        except Exception as e:
            print(f"❌ mplay32播放失败: {e}")
        
        # 方法6: 最后的尝试 - 使用os.startfile
        try:
            print(f"🔊 使用os.startfile打开: {audio_file}")
            os.startfile(audio_file)
            print(f"✅ os.startfile打开成功")
            if block:
                # 简单等待几秒，让音频播放
                print(f"⏳ 等待音频播放...") 
                time.sleep(5)  # 简单等待
            return True
        except Exception as e:
            print(f"❌ os.startfile打开失败: {e}")
            return False
    
    @staticmethod
    def _play_macos(audio_file, block):
        """macOS 平台播放音频"""
        cmd = ['afplay', audio_file]
        if block:
            subprocess.run(cmd, check=True)
        else:
            subprocess.Popen(cmd)
        return True
    
    @staticmethod
    def _play_linux(audio_file, block):
        """Linux 平台播放音频"""
        # 尝试多种播放器
        players = [
            ['aplay', audio_file],
            ['paplay', audio_file],
            ['ffplay', '-nodisp', '-autoexit', audio_file],
            ['mpg123', audio_file],
            ['play', audio_file]  # SoX
        ]
        
        for cmd in players:
            try:
                if block:
                    subprocess.run(cmd, check=True, capture_output=True)
                else:
                    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return True
            except Exception:
                continue
        
        return False


def play_audio_async(audio_file, delete_after=True):
    """
    异步播放音频并可选择播放后删除
    
    Args:
        audio_file: 音频文件路径
        delete_after: 是否在播放后删除文件
    """
    def _play_and_cleanup():
        print(f"🎵 开始播放音频: {audio_file}")
        
        if not os.path.exists(audio_file):
            print(f"❌ 音频文件不存在: {audio_file}")
            return
            
        success = AudioPlayer.play(audio_file, block=True)
        
        if success:
            print(f"✅ 音频播放完成: {audio_file}")
        else:
            print(f"❌ 音频播放失败: {audio_file}")
        
        if delete_after and os.path.exists(audio_file):
            # 等待一小段时间确保文件句柄已释放
            print(f"⏳ 等待文件句柄释放...")
            time.sleep(1.0)  # 增加等待时间
            try:
                os.remove(audio_file)
                print(f"🗑️ 已删除临时音频文件：{audio_file}")
            except Exception as e:
                print(f"⚠️ 删除音频文件失败: {e}")
                # 尝试再次删除
                try:
                    time.sleep(2.0)
                    os.remove(audio_file)
                    print(f"🗑️ 延迟删除成功：{audio_file}")
                except Exception as e2:
                    print(f"❌ 延迟删除仍然失败: {e2}")
    
    thread = threading.Thread(target=_play_and_cleanup)
    thread.daemon = True
    thread.start()
    
    return thread


if __name__ == "__main__":
    # 测试代码
    test_file = "test.mp3"
    if os.path.exists(test_file):
        print(f"测试播放音频文件: {test_file}")
        AudioPlayer.play(test_file, block=True)