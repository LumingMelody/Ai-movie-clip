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
        try:
            # 方法1: 使用 Windows Media Player COM 对象
            import win32com.client
            import pythoncom
            
            print(f"🔊 尝试Windows COM音频播放: {audio_file}")
            
            # 初始化COM
            pythoncom.CoInitialize()
            try:
                wmp = win32com.client.Dispatch("WMPlayer.OCX")
                
                # 设置音量为最大
                wmp.settings.volume = 100
                print(f"🔊 设置音量为: {wmp.settings.volume}")
                
                # 加载并播放音频
                wmp.URL = audio_file
                wmp.controls.play()
                
                # 等待播放器准备就绪
                time.sleep(0.5)
                
                print(f"✅ Windows COM播放启动成功")
                print(f"🎵 播放状态: {wmp.playState}, 文件: {wmp.currentMedia.name if wmp.currentMedia else 'Unknown'}")
                
                if block:
                    # 等待播放完成 (状态码: 1=停止, 2=暂停, 3=播放, 6=缓冲, 7=等待, 8=准备就绪, 9=重连, 10=就绪)
                    max_wait = 30  # 最多等待30秒
                    waited = 0
                    while wmp.playState != 1 and waited < max_wait:
                        time.sleep(0.2)
                        waited += 0.2
                        if waited % 2 == 0:  # 每2秒打印一次状态
                            print(f"📊 播放状态: {wmp.playState}, 已等待: {waited:.1f}s")
                    
                    if waited >= max_wait:
                        print(f"⏰ 播放超时，强制结束")
                    else:
                        print(f"✅ Windows COM播放完成")
                return True
            finally:
                # 清理COM
                pythoncom.CoUninitialize()
                
        except (ImportError, Exception) as e:
            print(f"❌ Windows COM播放失败: {e}")
            pass
        
        try:
            # 方法2: 使用 pygame
            import pygame
            
            print(f"🔊 尝试pygame音频播放: {audio_file}")
            
            # 初始化pygame mixer，如果已经初始化会自动跳过
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                print(f"🎮 pygame mixer初始化成功")
            else:
                print(f"🎮 pygame mixer已初始化: {pygame.mixer.get_init()}")
            
            # 设置音量
            pygame.mixer.music.set_volume(1.0)  # 最大音量
            
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            
            print(f"✅ pygame播放启动成功")
            
            if block:
                max_wait = 30  # 最多等待30秒
                waited = 0
                while pygame.mixer.music.get_busy() and waited < max_wait:
                    pygame.time.Clock().tick(10)
                    waited += 0.1
                    if int(waited) % 2 == 0 and waited - int(waited) < 0.1:  # 每2秒打印一次
                        print(f"📊 pygame播放中，已等待: {waited:.1f}s")
                
                if waited >= max_wait:
                    print(f"⏰ pygame播放超时，强制停止")
                    pygame.mixer.music.stop()
                else:
                    print(f"✅ pygame播放完成")
            return True
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
        
        # 方法4: 最后的尝试 - 使用默认程序打开
        try:
            os.startfile(audio_file)
            return True
        except:
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
            except:
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