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
        """
        Windows 平台播放音频
        
        优化顺序：
        1. PowerShell播放 - 最稳定有效
        2. Windows start命令 - 简单直接  
        3. os.startfile - 使用默认程序
        4. mplay32.exe - 备用方案
        
        已移除COM和pygame方法（在当前环境下不稳定）
        """
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
        # 方法1: 使用 Windows PowerShell 播放（最有效的方法）
        try:
            print(f"🔊 使用Windows PowerShell播放: {audio_file}")
            
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
            print(f"❌ PowerShell播放失败: {e}")
            pass
        
        # 方法2: 使用Windows start命令（第二有效的方法）
        try:
            print(f"🔊 使用Windows start命令播放: {audio_file}")
            
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
        
        # 方法3: 使用os.startfile（最简单的方法）
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
        
        # 方法4: 使用mplay32.exe（备用方法）
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