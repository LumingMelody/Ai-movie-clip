import socket
import threading
import random
import dashscope
from dashscope import Generation
from dashscope.audio.tts_v2 import SpeechSynthesizer
# from playsound import playsound  # 已替换为跨平台音频播放器

from .audio_player import AudioPlayer, play_audio_async
import json
import time
import os
import asyncio
import websockets
from typing import Dict, Any


# ================== 常量配置 ==================
class Constants:
    """系统常量配置类"""

    # API配置
    DEFAULT_API_KEY = 'sk-a48a1d84e015410292d07021f60b9acb'
    QWEN_MODEL = "qwen-max"
    COSYVOICE_MODEL = "cosyvoice-v2"
    COSYVOICE_V1_MODEL = "cosyvoice-v1"

    # 文件和目录
    CONFIG_DIR = "live_config/"
    PRODUCT_CONFIG_FILE = "product_config.json"
    VOICE_CONFIG_FILE = "voice_config.json"
    VOICE_ID_FILE = "xiaozong_voice_id.txt"
    VOICE_FILE_NAME = "xiao_zong.m4a"

    # 网络配置
    DEFAULT_HOST = '0.0.0.0'
    DEFAULT_PORT = 8888
    WEBSOCKET_PING_INTERVAL = 30
    WEBSOCKET_PING_TIMEOUT = 20
    WEBSOCKET_CLOSE_TIMEOUT = 60

    # 回复策略
    DEFAULT_REPLY_PROBABILITY = 0.3
    DEFAULT_MAX_QUEUE_SIZE = 5
    DEFAULT_REPLY_INTERVAL = 15
    MIN_QUEUE_FOR_REPLY = 1

    # 自动介绍
    NO_MESSAGE_TIMEOUT = 90
    AUTO_INTRODUCE_INTERVAL = 120
    ESTIMATED_WORDS_PER_SECOND = 2.5
    MAX_REPLY_LENGTH = 25
    TARGET_DURATION_SECONDS = 10

    # 重连配置
    MAX_RECONNECT_ATTEMPTS = 10
    RECONNECT_DELAY = 5

    # OSS配置
    OSS_ENDPOINT = 'https://oss-cn-hangzhou.aliyuncs.com'
    OSS_BUCKET_NAME = 'lan8-e-business'
    OSS_VOICE_PREFIX = 'voice_cloning/xiao_zong_'
    VOICE_CLONE_PREFIX = "xiaozong"

    # 语音选项
    VOICE_OPTIONS = {
        "female": "longanran",
        "male": "longlaotie_v2",
        "default": "longxiaochun_v2"
    }

    # 默认产品配置
    DEFAULT_PRODUCT_CONFIG = {
        "product_name": "智能健康手环",
        "price": 199,
        "features": "心率监测 睡眠分析 运动记录 防水设计",
        "discount": "85折"
    }

    # 默认语音配置
    DEFAULT_VOICE_CONFIG = {
        "model": "cosyvoice-v2",
        "voice": "longxiaochun_v2",
        "gender": "default",
        "speed": 1.0,
        "pitch": 1.0
    }

    # 错误消息
    ERROR_MESSAGES = {
        "qwen_error": "抱歉，我现在无法回答这个问题，请稍后再试。",
        "api_key_missing": "❌ 请先设置您的 DashScope API Key!",
        "oss_dependency_missing": "⚠️ 缺少OSS依赖，请安装: pip install oss2"
    }


# 设置 DashScope API Key
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY', Constants.DEFAULT_API_KEY)

# 配置文件路径
CONFIG_DIR = Constants.CONFIG_DIR
PRODUCT_CONFIG_FILE = os.path.join(CONFIG_DIR, Constants.PRODUCT_CONFIG_FILE)
VOICE_CONFIG_FILE = os.path.join(CONFIG_DIR, Constants.VOICE_CONFIG_FILE)

# 确保配置目录存在
os.makedirs(CONFIG_DIR, exist_ok=True)


# ================== 配置管理器 ==================
class ConfigManager:
    """配置管理器 - 支持文件持久化存储"""

    def __init__(self):
        self.product_info = self.load_product_config()
        self.voice_config = self.load_voice_config()
        self.voice_options = Constants.VOICE_OPTIONS
        print("✅ 配置管理器初始化完成")
        print(f"📦 产品配置: {self.product_info}")
        print(f"🎵 语音配置: {self.voice_config}")

    def load_product_config(self) -> Dict[str, Any]:
        """加载产品配置"""
        default_config = Constants.DEFAULT_PRODUCT_CONFIG

        try:
            if os.path.exists(PRODUCT_CONFIG_FILE):
                with open(PRODUCT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✅ 加载产品配置: {config}")
                return config
            else:
                print(f"📁 创建默认产品配置")
                self.save_product_config(default_config)
                return default_config
        except Exception as e:
            print(f"⚠️ 加载产品配置失败，使用默认配置: {e}")
            return default_config

    def load_voice_config(self) -> Dict[str, Any]:
        """加载语音配置"""
        default_config = Constants.DEFAULT_VOICE_CONFIG

        try:
            if os.path.exists(VOICE_CONFIG_FILE):
                with open(VOICE_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✅ 加载语音配置: {config}")
                return config
            else:
                print(f"📁 创建默认语音配置")
                self.save_voice_config(default_config)
                return default_config
        except Exception as e:
            print(f"⚠️ 加载语音配置失败，使用默认配置: {e}")
            return default_config

    def save_product_config(self, config: Dict[str, Any]) -> bool:
        """保存产品配置"""
        try:
            with open(PRODUCT_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            print(f"💾 产品配置已保存: {config}")
            return True
        except Exception as e:
            print(f"❌ 保存产品配置失败: {e}")
            return False

    def save_voice_config(self, config: Dict[str, Any]) -> bool:
        """保存语音配置"""
        try:
            with open(VOICE_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            print(f"💾 语音配置已保存: {config}")
            return True
        except Exception as e:
            print(f"❌ 保存语音配置失败: {e}")
            return False

    def update_product_config(self, updates: Dict[str, Any]) -> bool:
        """更新产品配置"""
        try:
            # 更新配置
            self.product_info.update(updates)

            # 保存到文件
            if self.save_product_config(self.product_info):
                print(f"✅ 产品配置更新成功: {updates}")
                return True
            else:
                return False
        except Exception as e:
            print(f"❌ 更新产品配置失败: {e}")
            return False

    def update_voice_config(self, updates: Dict[str, Any]) -> bool:
        """更新语音配置"""
        try:
            # 特殊处理性别变化
            if "gender" in updates:
                gender = updates["gender"]
                if gender in self.voice_options:
                    updates["voice"] = self.voice_options[gender]
                    print(f"🔄 根据性别 '{gender}' 自动选择语音: {updates['voice']}")

            # 更新配置
            self.voice_config.update(updates)

            # 保存到文件
            if self.save_voice_config(self.voice_config):
                print(f"✅ 语音配置更新成功: {updates}")
                return True
            else:
                return False
        except Exception as e:
            print(f"❌ 更新语音配置失败: {e}")
            return False

    def set_voice_gender(self, gender: str) -> bool:
        """设置语音性别"""
        if gender in self.voice_options:
            return self.update_voice_config({"gender": gender})
        else:
            available_options = list(self.voice_options.keys())
            print(f"❌ 无效的语音性别选择: {gender}，可选项: {available_options}")
            return False

    def get_current_voice(self) -> str:
        """获取当前使用的语音"""
        return self.voice_config.get("voice", Constants.VOICE_OPTIONS["default"])

    def get_voice_params(self) -> Dict[str, Any]:
        """获取语音合成参数"""
        return {
            "model": self.voice_config.get("model", Constants.COSYVOICE_MODEL),
            "voice": self.get_current_voice(),
            "speed": self.voice_config.get("speed", 1.0),
            "pitch": self.voice_config.get("pitch", 1.0)
        }

    def get_voice_options_info(self) -> Dict[str, Any]:
        """获取所有可用的语音选项信息"""
        return {
            "voice_options": {
                "female": {
                    "name": "longanran",
                    "description": "女声 - 温柔甜美"
                },
                "male": {
                    "name": "longlaotie_v2",
                    "description": "男声 - 成熟稳重"
                },
                "default": {
                    "name": "longxiaochun_v2",
                    "description": "默认声音 - 自然清晰"
                }
            },
            "current_selection": self.voice_config["gender"],
            "current_voice": self.voice_config["voice"]
        }

    def reload_configs(self) -> bool:
        """重新加载所有配置"""
        try:
            self.product_info = self.load_product_config()
            self.voice_config = self.load_voice_config()
            print("🔄 配置重新加载完成")
            return True
        except Exception as e:
            print(f"❌ 配置重新加载失败: {e}")
            return False


# 创建全局配置管理器实例
config_manager = ConfigManager()


# ================== 语音生成服务 ==================
class AudioService:
    """统一的语音生成服务 - 支持普通合成和声音克隆"""

    def __init__(self, use_voice_cloning=False):
        self.use_voice_cloning = use_voice_cloning
        self.cached_voice_id = None

        if self.use_voice_cloning:
            print(f"🎤 AudioService: 已启用声音克隆模式（使用本地xiao_zong.m4a）")
            self._load_cached_voice_id()

    def _load_cached_voice_id(self):
        """加载缓存的voice_id"""
        try:
            voice_id_file = os.path.join(CONFIG_DIR, "xiaozong_voice_id.txt")
            if os.path.exists(voice_id_file):
                with open(voice_id_file, 'r') as f:
                    self.cached_voice_id = f.read().strip()
                print(f"📂 AudioService: 已加载保存的voice_id: {self.cached_voice_id}")
        except Exception as load_error:
            print(f"⚠️ AudioService: 加载voice_id失败: {load_error}")

    def _find_local_voice_file(self):
        """查找本地语音文件"""
        possible_paths = [
            "xiao_zong.m4a",  # 当前目录
            os.path.join(os.path.dirname(__file__), "xiao_zong.m4a"),  # 同目录
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "xiao_zong.m4a"),
            # 项目根目录
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def _create_voice_clone(self, local_voice_path):
        """创建声音克隆"""
        from dashscope.audio.tts_v2 import VoiceEnrollmentService
        import oss2
        import uuid

        # OSS配置
        access_key_id = os.getenv('OSS_ACCESS_KEY_ID', '')
        access_key_secret = os.getenv('OSS_ACCESS_KEY_SECRET', '')
        endpoint = 'https://oss-cn-hangzhou.aliyuncs.com'
        bucket_name = 'lan8-e-business'

        print("🎯 第一步：上传参考音频到OSS...")

        # 创建OSS客户端
        auth = oss2.Auth(access_key_id, access_key_secret)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)

        # 生成唯一的对象名
        object_name = f"voice_cloning/xiao_zong_{uuid.uuid4()}.m4a"

        # 上传本地音频文件到OSS
        result = bucket.put_object_from_file(object_name, local_voice_path)

        if result.status != 200:
            raise Exception(f"OSS上传失败，状态码: {result.status}")

        reference_url = f"https://{bucket_name}.{endpoint.replace('https://', '')}/{object_name}"
        print(f"✅ OSS上传成功: {reference_url}")

        print("🎯 第二步：创建声音克隆...")

        # 创建语音注册服务实例
        service = VoiceEnrollmentService()

        # 调用create_voice方法复刻声音
        voice_id = service.create_voice(
            target_model="cosyvoice-v1",
            prefix="xiaozong",
            url=reference_url
        )

        print(f"✅ 声音克隆创建成功，voice_id: {voice_id}")

        # 缓存voice_id
        self.cached_voice_id = voice_id

        # 保存voice_id到文件
        try:
            voice_id_file = os.path.join(CONFIG_DIR, "xiaozong_voice_id.txt")
            with open(voice_id_file, 'w') as f:
                f.write(voice_id)
            print(f"📝 已保存voice_id到文件: {voice_id_file}")
        except Exception as save_error:
            print(f"⚠️ 保存voice_id失败: {save_error}")

        return voice_id

    def _generate_cloned_audio(self, text, voice_id):
        """使用克隆音色生成语音"""
        print("🎯 使用克隆音色合成语音...")

        synthesizer = SpeechSynthesizer(
            model="cosyvoice-v1",
            voice=voice_id
        )

        audio_data = synthesizer.call(text)
        audio_filename = f"audio_response_cloned_{int(time.time())}_{random.randint(1000, 9999)}.mp3"

        with open(audio_filename, 'wb') as f:
            f.write(audio_data)

        print(f"🎉 OSS声音克隆合成成功: {audio_filename}")
        return audio_filename

    def _generate_normal_audio(self, text):
        """使用普通配置生成语音"""
        voice_params = config_manager.get_voice_params()
        print(f"🎵 使用普通语音配置: {voice_params}")

        synthesizer = SpeechSynthesizer(
            model=voice_params["model"],
            voice=voice_params["voice"]
        )

        audio_data = synthesizer.call(text)
        audio_filename = f"audio_response_{int(time.time())}_{random.randint(1000, 9999)}.mp3"

        with open(audio_filename, 'wb') as f:
            f.write(audio_data)

        print(f"✅ 普通语音合成成功: {audio_filename} (语音: {voice_params['voice']})")
        return audio_filename

    def generate_audio(self, text):
        """生成语音音频，根据配置决定是否使用声音克隆"""
        try:
            # 检查是否启用声音克隆
            if self.use_voice_cloning:
                local_voice_path = self._find_local_voice_file()

                print(
                    f"🔍 声音克隆检查: use_voice_cloning={self.use_voice_cloning}, 找到文件={local_voice_path is not None}")
                if local_voice_path:
                    print(f"📍 音频文件路径: {os.path.abspath(local_voice_path)}")

                if local_voice_path:
                    print(f"🎤 检测到本地语音文件: {local_voice_path}，使用OSS声音克隆模式")

                    try:
                        # 检查是否有缓存的voice_id
                        if self.cached_voice_id:
                            print(f"🎯 使用缓存的voice_id: {self.cached_voice_id}")
                            voice_id = self.cached_voice_id
                        else:
                            # 首次使用，需要创建声音克隆
                            voice_id = self._create_voice_clone(local_voice_path)

                        return self._generate_cloned_audio(text, voice_id)

                    except ImportError as ie:
                        print(f"⚠️ 缺少OSS依赖: {str(ie)}，请安装: pip install oss2")
                    except Exception as clone_error:
                        print(f"⚠️ OSS声音克隆失败: {str(clone_error)}，回退到普通合成")

            # 普通语音合成模式
            return self._generate_normal_audio(text)

        except Exception as e:
            print(f"❌ 语音合成错误: {e}")
            return None


# 创建全局音频服务实例
audio_service = AudioService()


# ================== AI生成服务 ==================
class AIService:
    """统一的AI服务 - 处理文本生成和提示词构建"""

    @staticmethod
    def build_prompt(message: str) -> str:
        """构建提示词，使用最新的产品配置，生成简短回复"""
        current_product = config_manager.product_info
        features_str = ', '.join(current_product['features']) if isinstance(current_product['features'], list) else \
        current_product['features']

        return (
            f"你是一个销售代理，推广产品：{current_product['product_name']}，"
            f"价格：{current_product['price']}元，特点：{features_str}，"
            f"当前折扣：{current_product['discount']}。"
            f"请用简短自然的语言回答客户的问题：{message}。"
            f"要求：回复必须控制在{Constants.MAX_REPLY_LENGTH}字以内，语言要亲切自然，适合语音播放，时长约{Constants.TARGET_DURATION_SECONDS}秒。"
        )

    @staticmethod
    def generate_with_qwen(prompt: str) -> str:
        """调用Qwen生成回复"""
        try:
            response = Generation.call(
                model=Constants.QWEN_MODEL,
                prompt=prompt,
                result_format='message'
            )
            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                return Constants.ERROR_MESSAGES["qwen_error"]
        except Exception as e:
            print(f"❌ Qwen生成错误: {e}")
            return Constants.ERROR_MESSAGES["qwen_error"]

    @staticmethod
    def get_priority_replies() -> Dict[str, str]:
        """获取优先回复模板"""
        return {
            "价格": "我们的{product_name}当前优惠价是{price}元，比原价便宜了{discount}。",
            "功能": "这款{product_name}具有{features}等功能。",
            "优惠": "现在购买可以享受{discount}优惠，这是本月特别活动。",
            "质量": "我们提供一年质保，所有产品都通过严格的质量检测。"
        }

    @staticmethod
    def process_message(message: str) -> str:
        """根据内容决定优先回复还是调用Qwen"""
        current_product = config_manager.product_info
        priority_replies = AIService.get_priority_replies()

        for key in priority_replies:
            if key in message:
                # 处理features列表的显示
                formatted_info = current_product.copy()
                if isinstance(formatted_info['features'], list):
                    formatted_info['features'] = '、'.join(formatted_info['features'])
                return priority_replies[key].format(**formatted_info)

        return AIService.generate_with_qwen(AIService.build_prompt(message))


# 创建全局AI服务实例
ai_service = AIService()


# ================== WebSocket 客户端 ==================
class WebSocketClient:
    """WebSocket客户端 - 用于连接虚拟机上的WebSocket服务器并处理消息"""

    def __init__(self, host='10.211.55.3', port=Constants.DEFAULT_PORT,
                 reply_probability=Constants.DEFAULT_REPLY_PROBABILITY,
                 max_queue_size=Constants.DEFAULT_MAX_QUEUE_SIZE, use_voice_cloning=False,
                 reply_interval=Constants.DEFAULT_REPLY_INTERVAL):
        self.host = host
        self.port = port
        self.uri = f"ws://{host}:{port}"
        self.websocket = None
        self.connected = False
        self.running = False
        self.listen_task = None

        # 消息队列和随机回复设置
        self.message_queue = []
        self.max_queue_size = max_queue_size  # 最大消息队列长度
        self.reply_probability = reply_probability  # 回复概率
        self.min_queue_for_reply = Constants.MIN_QUEUE_FOR_REPLY  # 至少有1条消息才考虑回复
        self.use_voice_cloning = use_voice_cloning  # 🔥 新增：控制是否使用声音克隆
        self.cached_voice_id = None  # 🔥 缓存voice_id，避免重复克隆

        # 回复时间间隔控制
        self.reply_interval = reply_interval  # 两次回复之间的最小间隔（秒）
        self.last_reply_time = 0  # 上次回复的时间戳

        print(
            f"🎯 随机回复设置: 回复概率={reply_probability * 100:.1f}%, 最大队列长度={max_queue_size}, 回复间隔={reply_interval}秒")
        if self.use_voice_cloning:
            print(f"🎤 已启用声音克隆模式（使用本地xiao_zong.m4a）")

            # 🔥 尝试加载已保存的voice_id
            try:
                voice_id_file = os.path.join(CONFIG_DIR, "xiaozong_voice_id.txt")
                if os.path.exists(voice_id_file):
                    with open(voice_id_file, 'r') as f:
                        self.cached_voice_id = f.read().strip()
                    print(f"📂 已加载保存的voice_id: {self.cached_voice_id}")
            except Exception as load_error:
                print(f"⚠️ 加载voice_id失败: {load_error}")

        # 优先回复模板（由AIService统一管理）
        self.priority_replies = ai_service.get_priority_replies()

        # 降级方案设置
        self.last_message_time = time.time()  # 上次收到消息的时间
        self.no_message_timeout = 90  # 90秒没有弹幕就触发降级（考虑到介绍本身需要30-45秒）
        self.auto_introduce_task = None  # 自动介绍任务
        self.auto_introduce_interval = 120  # 自动介绍间隔（秒），避免太频繁
        self.last_auto_introduce_time = 0  # 上次自动介绍的时间

        # AI生成介绍的提示词索引
        self.intro_template_index = 0  # 当前使用的提示词索引

        # 重连设置
        self.auto_reconnect = True  # 是否自动重连
        self.max_reconnect_attempts = 10  # 最大重连次数
        self.reconnect_delay = 5  # 重连延迟（秒）
        self.reconnect_task = None  # 重连任务

    def is_connected(self):
        """检查是否连接"""
        return self.connected and self.websocket is not None

    async def connect(self):
        """连接到WebSocket服务器"""
        try:
            print(f"🔌 正在连接到WebSocket服务器 {self.uri}...")
            # 增加ping_interval和ping_timeout来保持连接
            self.websocket = await websockets.connect(
                self.uri,
                ping_interval=30,  # 每30秒发送ping（不要太频繁）
                ping_timeout=20,  # 20秒内没有收到pong就认为连接断开
                close_timeout=60  # 增加关闭超时时间
            )
            self.connected = True
            self.running = True
            print(f"✅ 已连接到WebSocket服务器 {self.uri}")

            # 启动消息监听任务
            self.listen_task = asyncio.create_task(self._listen_loop())

            # 启动自动介绍任务
            self.auto_introduce_task = asyncio.create_task(self._auto_introduce_loop())

            # 启动重连监控任务
            if self.auto_reconnect:
                self.reconnect_task = asyncio.create_task(self._reconnect_monitor())

            print(
                f"🤖 自动介绍功能已启动 - 无弹幕超时: {self.no_message_timeout}秒, 介绍间隔: {self.auto_introduce_interval}秒")
            print(f"📡 WebSocket保活设置 - Ping间隔: 30秒, Ping超时: 20秒")
            print(f"🔄 自动重连已启用 - 最大重试: {self.max_reconnect_attempts}次, 重连延迟: {self.reconnect_delay}秒")

            return True

        except Exception as e:
            print(f"❌ 连接WebSocket服务器失败: {e}")
            self.connected = False
            self.running = False
            return False

    async def close(self):
        """关闭连接"""
        try:
            self.running = False
            self.connected = False

            if self.listen_task:
                self.listen_task.cancel()
                try:
                    await self.listen_task
                except asyncio.CancelledError:
                    pass

            if self.auto_introduce_task:
                self.auto_introduce_task.cancel()
                try:
                    await self.auto_introduce_task
                except asyncio.CancelledError:
                    pass

            if self.reconnect_task:
                self.reconnect_task.cancel()
                try:
                    await self.reconnect_task
                except asyncio.CancelledError:
                    pass

            if self.websocket:
                await self.websocket.close()
                self.websocket = None

            # 清理可能残留的临时音频文件
            self._cleanup_temp_audio_files()

            print("🔌 WebSocket客户端已断开连接")
            return True

        except Exception as e:
            print(f"❌ 断开WebSocket连接失败: {e}")
            return False

    async def send_message(self, message):
        """发送消息到WebSocket服务器"""
        if not self.connected or not self.websocket:
            print("⚠️ 未连接到WebSocket服务器")
            return False

        try:
            await self.websocket.send(message)
            print(f"📤 发送消息到WebSocket服务器: {message}")
            return True

        except Exception as e:
            print(f"❌ 发送消息失败: {e}")
            return False

    async def _listen_loop(self):
        """消息监听循环"""
        try:
            while self.running:
                try:
                    message = await self.websocket.recv()
                    # print(f"📥 收到来自WebSocket服务器的消息: {message}")

                    # 处理接收到的消息
                    await self._process_received_message(message)

                except websockets.exceptions.ConnectionClosed as e:
                    print(f"🔌 WebSocket连接已关闭: {e}")
                    if hasattr(e, 'rcvd'):
                        print(f"关闭代码: {e.rcvd.code if e.rcvd else 'N/A'}")
                        print(f"关闭原因: {e.rcvd.reason if e.rcvd else 'N/A'}")
                    self.connected = False
                    # 不要设置 self.running = False，让主程序决定是否重连
                    break
                except Exception as e:
                    print(f"❌ 接收消息失败: {e}")
                    await asyncio.sleep(1)

        except asyncio.CancelledError:
            print("📴 消息监听任务已取消")
        except Exception as e:
            print(f"❌ 消息监听错误: {e}")
            self.connected = False
            # 不要设置 self.running = False，让主程序决定是否重连

    async def _process_received_message(self, message):
        """处理接收到的消息并生成智能回复"""
        try:
            # 解析消息
            try:
                data = json.loads(message)
                msg_type = data.get('Type')

                # 处理Type为3的进入直播间消息
                if msg_type == 3:
                    # 解析Data字段中的JSON
                    data_str = data.get('Data', '{}')
                    try:
                        data_content = json.loads(data_str)
                        user_info = data_content.get('User', {})
                        nickname = user_info.get('Nickname', '用户')

                        print(f"👋 用户进入直播间: {nickname}")

                        # 随机决定是否欢迎（30%概率）
                        if random.random() < 0.3:
                            welcome_messages = [
                                f"欢迎{nickname}来到直播间！今天有特别优惠哦",
                                f"欢迎{nickname}！正好赶上我们的活动",
                                f"欢迎{nickname}进入直播间，有什么想了解的可以问我",
                                f"{nickname}你好！欢迎来看我们的产品介绍",
                                f"欢迎新朋友{nickname}！今天有惊喜价格"
                            ]

                            welcome_text = random.choice(welcome_messages)
                            print(f"🎉 发送欢迎语: {welcome_text}")

                            # 生成语音
                            audio_file = self.generate_audio(welcome_text)

                            # 播放语音
                            if audio_file and os.path.exists(audio_file):
                                print(f"🎵 正在播放欢迎语音：{audio_file}")
                                try:
                                    play_audio_async(audio_file, delete_after=True)
                                    print("✅ 欢迎语音播放任务已启动")
                                except Exception as e:
                                    print(f"❌ 播放欢迎语音失败: {e}")
                                    try:
                                        os.remove(audio_file)
                                    except:
                                        pass

                            # 构建欢迎消息
                            welcome_message = {
                                "type": "welcome_message",
                                "user": nickname,
                                "message": welcome_text,
                                "voice_used": config_manager.get_current_voice(),
                                "timestamp": time.time()
                            }

                            # 发送欢迎消息到WebSocket服务器
                            await self.send_message(json.dumps(welcome_message, ensure_ascii=False))
                        else:
                            print(f"🤐 跳过欢迎语（随机选择）")

                    except json.JSONDecodeError:
                        print(f"⚠️ 无法解析Type=3的Data字段: {data_str}")

                    return

                # 只处理Type为1的消息
                if msg_type != 1:
                    # print(f"📨 忽略非Type=1的消息: Type={msg_type}")
                    return

                # 解析Data字段中的JSON
                data_str = data.get('Data', '{}')
                try:
                    data_content = json.loads(data_str)
                    content = data_content.get('Content', '')
                    user_info = data_content.get('User', {})
                    nickname = user_info.get('Nickname', '用户')

                    print(f"📨 收到直播消息 [用户: {nickname}]: {content}")

                except json.JSONDecodeError:
                    print(f"⚠️ 无法解析Data字段: {data_str}")
                    return

            except json.JSONDecodeError:
                print(f"⚠️ 无法解析消息JSON: {message}")
                return

            # 如果content为空，不处理
            if not content.strip():
                print("📨 消息内容为空，跳过处理")
                return

            # 更新最后消息时间
            self.last_message_time = time.time()

            # 将消息添加到队列
            message_data = {
                "content": content,
                "nickname": nickname,
                "timestamp": time.time()
            }

            self.message_queue.append(message_data)
            print(f"📝 消息已加入队列，当前队列长度: {len(self.message_queue)}")

            # 如果队列超过最大长度，移除最旧的消息
            if len(self.message_queue) > self.max_queue_size:
                removed = self.message_queue.pop(0)
                print(f"🗑️ 队列已满，移除最旧消息: [{removed['nickname']}]: {removed['content']}")

            # 随机决定是否回复
            if len(self.message_queue) >= self.min_queue_for_reply:
                current_time = time.time()
                time_since_last_reply = current_time - self.last_reply_time

                # 检查时间间隔
                if time_since_last_reply < self.reply_interval:
                    remaining_time = self.reply_interval - time_since_last_reply
                    print(f"⏰ 回复间隔未达到，还需等待 {remaining_time:.1f} 秒")
                    return

                # 生成随机数判断是否回复
                should_reply = random.random() < self.reply_probability

                if should_reply:
                    # 从队列中随机选择一条消息进行回复
                    selected_message = random.choice(self.message_queue)
                    print(
                        f"🎯 随机选中消息进行回复 [用户: {selected_message['nickname']}]: {selected_message['content']}")

                    # 回复选中的消息
                    await self._generate_and_send_reply(selected_message)

                    # 更新最后回复时间
                    self.last_reply_time = current_time

                    # 清空消息队列
                    self.message_queue.clear()
                    print("🧹 消息队列已清空")
                else:
                    print(f"🎲 随机决定不回复 (概率: {self.reply_probability * 100:.1f}%)")

        except Exception as e:
            print(f"❌ 处理接收消息时出错: {e}")

    async def _generate_and_send_reply(self, message_data):
        """生成并发送回复"""
        try:
            content = message_data["content"]
            nickname = message_data["nickname"]

            # 生成智能回复
            reply_text = self.process_message(content)

            # 生成语音
            audio_file = self.generate_audio(reply_text)

            # 播放语音
            if audio_file and os.path.exists(audio_file):
                print(f"🎵 正在播放AI回复音频：{audio_file}")
                try:
                    # 使用跨平台音频播放器
                    play_audio_async(audio_file, delete_after=True)
                    print("✅ 音频播放任务已启动")

                except Exception as e:
                    print(f"❌ 播放音频失败: {e}")
                    # 即使播放失败也尝试删除文件
                    try:
                        os.remove(audio_file)
                        print(f"🗑️ 已删除音频文件：{audio_file}")
                    except Exception as delete_error:
                        print(f"⚠️ 删除音频文件失败: {delete_error}")

            # 构建回复消息
            reply_message = {
                "type": "ai_reply",
                "original_message": content,
                "reply": reply_text,
                "user": nickname,
                "voice_used": config_manager.get_current_voice(),
                "timestamp": time.time()
            }

            # 发送回复到WebSocket服务器
            await self.send_message(json.dumps(reply_message, ensure_ascii=False))

        except Exception as e:
            print(f"❌ 生成和发送回复时出错: {e}")

    async def _auto_introduce_loop(self):
        """自动介绍循环 - 在没有弹幕时定期介绍产品"""
        try:
            await asyncio.sleep(10)  # 初始等待10秒

            while self.running:
                current_time = time.time()
                time_since_last_message = current_time - self.last_message_time
                time_since_last_intro = current_time - self.last_auto_introduce_time

                # 如果超过指定时间没有收到弹幕，且距离上次自动介绍已过间隔时间
                if (time_since_last_message > self.no_message_timeout and
                        time_since_last_intro > self.auto_introduce_interval):
                    print(f"⏰ {self.no_message_timeout}秒内没有收到弹幕，触发自动产品介绍")

                    # 生成产品介绍
                    await self._generate_auto_introduction()

                    # 更新最后自动介绍时间
                    self.last_auto_introduce_time = current_time

                # 每5秒检查一次
                await asyncio.sleep(5)

        except asyncio.CancelledError:
            print("📴 自动介绍任务已取消")
        except Exception as e:
            print(f"❌ 自动介绍循环错误: {e}")

    async def _generate_auto_introduction(self):
        """生成并播放自动产品介绍"""
        try:
            # 获取当前产品配置
            current_product = config_manager.product_info

            # 构建AI生成介绍的提示词（10秒左右的简短介绍）
            intro_prompts = [
                f"你是一个专业的直播间主播，正在销售{current_product['product_name']}。请生成一段10秒左右的简短产品介绍，要包含核心卖点和优惠信息。语气要亲切自然，25字以内。",
                f"作为一个带货主播，请为{current_product['product_name']}创作一句话介绍。重点突出产品特色和价格优势，控制在25字以内，时长约10秒。",
                f"你正在直播卖货，现在需要简单介绍{current_product['product_name']}。用一句话说出产品亮点和优惠，让观众快速了解，25字以内。",
                f"请扮演一个热情的直播间主播，用最简洁的话介绍{current_product['product_name']}的独特卖点，25字以内，适合10秒语音播放。",
                f"现在直播间需要活跃气氛，请用简短话语介绍{current_product['product_name']}的核心价值和优惠，25字以内，语音播放约10秒。"
            ]

            # 随机选择一个提示词风格
            prompt_template = intro_prompts[self.intro_template_index % len(intro_prompts)]

            # 构建完整的提示词
            features_str = '、'.join(current_product['features']) if isinstance(current_product['features'], list) else \
                current_product['features']

            full_prompt = f"{prompt_template}\n\n产品信息：\n- 产品名称：{current_product['product_name']}\n- 价格：{current_product['price']}元\n- 当前优惠：{current_product['discount']}\n- 主要特点：{features_str}\n\n要求：直接生成介绍词，不要开场白或结束语，严格控制在25字以内，适合10秒语音播放。"

            # 使用AI生成介绍文本
            print(f"🤖 正在使用AI生成产品介绍...")
            intro_text = self.generate_with_qwen(full_prompt)

            # 更新模板索引（循环使用）
            self.intro_template_index = (self.intro_template_index + 1) % len(intro_prompts)

            # 计算大概的播放时长（按照中文每秒2.5个字计算，目标10秒）
            estimated_duration = len(intro_text) / 2.5
            print(f"🎯 简短自动产品介绍 (预计时长: {estimated_duration:.1f}秒):\n{intro_text}")

            # 生成语音
            audio_file = self.generate_audio(intro_text)

            # 播放语音
            if audio_file and os.path.exists(audio_file):
                print(f"🎵 正在播放自动介绍音频：{audio_file}")

                # 使用改进的异步播放器，自动处理清理
                play_audio_async(audio_file, delete_after=True)

                # 给音频播放一点启动时间
                time.sleep(0.5)

            # 更新最后消息时间，避免在播放期间又触发新的介绍
            self.last_message_time = time.time()

            # 自动介绍完成，不需要发送到服务器
            print("✅ 自动产品介绍播放完成")

        except Exception as e:
            print(f"❌ 生成自动介绍时出错: {e}")

    async def _reconnect_monitor(self):
        """重连监控任务 - 监控连接状态并自动重连"""
        reconnect_attempts = 0

        try:
            while self.running and self.auto_reconnect:
                await asyncio.sleep(5)  # 每5秒检查一次连接状态

                # 如果连接断开了，尝试重连
                if not self.is_connected() and self.running:
                    if reconnect_attempts >= self.max_reconnect_attempts:
                        print(f"❌ 达到最大重连次数({self.max_reconnect_attempts})，停止重连")
                        break

                    reconnect_attempts += 1
                    print(f"🔄 检测到连接断开，开始第{reconnect_attempts}次重连...")

                    try:
                        # 先清理现有连接
                        if self.websocket:
                            try:
                                await self.websocket.close()
                            except:
                                pass
                            self.websocket = None

                        self.connected = False

                        # 等待一段时间再重连
                        await asyncio.sleep(self.reconnect_delay)

                        # 尝试重新连接
                        print(f"🔌 重新连接到WebSocket服务器 {self.uri}...")
                        self.websocket = await websockets.connect(
                            self.uri,
                            ping_interval=30,
                            ping_timeout=20,
                            close_timeout=60
                        )
                        self.connected = True

                        # 重新启动监听任务
                        if self.listen_task:
                            self.listen_task.cancel()
                            try:
                                await self.listen_task
                            except asyncio.CancelledError:
                                pass

                        self.listen_task = asyncio.create_task(self._listen_loop())

                        print(f"✅ 第{reconnect_attempts}次重连成功！")
                        reconnect_attempts = 0  # 重连成功，重置计数器

                    except Exception as reconnect_error:
                        print(f"❌ 第{reconnect_attempts}次重连失败: {reconnect_error}")
                        if reconnect_attempts >= self.max_reconnect_attempts:
                            print(f"❌ 重连失败次数过多，停止重连")
                            break

                # 如果连接正常，重置重连计数器
                elif self.is_connected():
                    if reconnect_attempts > 0:
                        reconnect_attempts = 0

        except asyncio.CancelledError:
            print("📴 重连监控任务已取消")
        except Exception as e:
            print(f"❌ 重连监控错误: {e}")

    def _cleanup_temp_audio_files(self):
        """清理临时音频文件"""
        try:
            import glob
            # 查找当前目录下的临时音频文件（以audio_response_开头的mp3文件）
            temp_files = glob.glob("audio_response_*.mp3")

            for file_path in temp_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"🗑️ 清理残留音频文件：{file_path}")
                except Exception as delete_error:
                    print(f"⚠️ 清理音频文件失败: {file_path} - {delete_error}")

            if temp_files:
                print(f"✅ 共清理 {len(temp_files)} 个临时音频文件")

        except Exception as e:
            print(f"❌ 清理临时音频文件时出错: {e}")

    def process_message(self, message):
        """根据内容决定优先回复还是调用Qwen，委托给AIService处理"""
        return ai_service.process_message(message)

    def build_prompt(self, message):
        """构建提示词，委托给AIService处理"""
        return ai_service.build_prompt(message)

    def generate_with_qwen(self, prompt):
        """调用Qwen生成回复，委托给AIService处理"""
        return ai_service.generate_with_qwen(prompt)

    def generate_audio(self, text):
        """生成语音音频，委托给AudioService处理"""
        return audio_service.generate_audio(text)


# ================== Socket 服务器 ==================
class SocketServer:
    def __init__(self, host='0.0.0.0', port=8888, use_voice_cloning=False):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = True
        self.message_queue = []
        self.use_voice_cloning = use_voice_cloning  # 🔥 新增：控制是否使用声音克隆
        self.cached_voice_id = None  # 🔥 缓存voice_id，避免重复克隆

        # 优先回复模板（由AIService统一管理）
        self.priority_replies = ai_service.get_priority_replies()

        if self.use_voice_cloning:
            print(f"🎤 [SocketServer] 已启用声音克隆模式（使用本地xiao_zong.m4a）")

            # 🔥 尝试加载已保存的voice_id
            try:
                voice_id_file = os.path.join(CONFIG_DIR, "xiaozong_voice_id.txt")
                if os.path.exists(voice_id_file):
                    with open(voice_id_file, 'r') as f:
                        self.cached_voice_id = f.read().strip()
                    print(f"📂 [SocketServer] 已加载保存的voice_id: {self.cached_voice_id}")
            except Exception as load_error:
                print(f"⚠️ [SocketServer] 加载voice_id失败: {load_error}")

    def start(self):
        import socket as sock

        # 验证IP地址是否可用
        if self.host not in ['0.0.0.0', '127.0.0.1', 'localhost']:
            try:
                # 尝试获取系统所有IP地址
                hostname = sock.gethostname()
                all_ips = sock.gethostbyname_ex(hostname)[2]

                # 添加一些常见的本地IP获取方式
                import subprocess
                try:
                    result = subprocess.run(['ifconfig'], capture_output=True, text=True)
                    import re
                    ips_from_ifconfig = re.findall(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
                    all_ips.extend(ips_from_ifconfig)
                except:
                    pass

                all_ips = list(set(all_ips))  # 去重

                if self.host not in all_ips:
                    print(f"⚠️ 警告: IP地址 {self.host} 不在系统网络接口中")
                    print(f"📋 可用的IP地址: {all_ips}")
                    print(f"🔄 将使用 0.0.0.0 来监听所有接口")
                    self.host = '0.0.0.0'
            except Exception as e:
                print(f"❌ 检查IP地址时出错: {e}")
                print(f"🔄 将使用 0.0.0.0 来监听所有接口")
                self.host = '0.0.0.0'

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"🚀 Socket服务器正在 {self.host}:{self.port} 监听...")
        except OSError as e:
            if e.errno == 49:  # Can't assign requested address
                print(f"❌ 无法绑定到 {self.host}:{self.port}")
                print(f"🔄 尝试使用 0.0.0.0:{self.port} 重新绑定...")
                self.host = '0.0.0.0'
                self.server_socket.bind((self.host, self.port))
                self.server_socket.listen(5)
                print(f"✅ Socket服务器正在 {self.host}:{self.port} 监听...")
            else:
                raise

        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"📞 来自 {addr} 的连接")
                client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_handler.daemon = True
                client_handler.start()
            except Exception as e:
                if self.running:
                    print(f"❌ 接受连接时出错: {e}")

    def handle_client(self, client_socket):
        try:
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    break

                try:
                    message = data.decode('utf-8')
                    print(f"📨 收到消息: {message}")

                    # 检查是否是配置更新命令
                    if self.handle_config_commands(client_socket, message):
                        continue

                    # 普通消息处理
                    self.message_queue.append((client_socket, message))

                    if len(self.message_queue) >= 1:
                        selected = random.choice(self.message_queue)
                        self.message_queue.clear()
                        self.process_and_respond(*selected)

                except UnicodeDecodeError:
                    print("⚠️ 消息解码失败")
                    continue

        except Exception as e:
            print(f"❌ 处理客户端消息时出错: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass

    def handle_config_commands(self, client_socket, message) -> bool:
        """处理配置更新命令"""
        try:
            # 尝试解析JSON命令
            if message.startswith("{") and message.endswith("}"):
                try:
                    command = json.loads(message)

                    if command.get("type") == "update_product":
                        data = command.get("data", {})
                        success = config_manager.update_product_config(data)
                        response = {
                            "type": "config_response",
                            "success": success,
                            "message": "产品配置更新成功" if success else "产品配置更新失败",
                            "data": config_manager.product_info
                        }
                        client_socket.sendall(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                        return True

                    elif command.get("type") == "update_voice":
                        data = command.get("data", {})
                        success = config_manager.update_voice_config(data)
                        response = {
                            "type": "config_response",
                            "success": success,
                            "message": "语音配置更新成功" if success else "语音配置更新失败",
                            "data": config_manager.voice_config
                        }
                        client_socket.sendall(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                        return True

                    elif command.get("type") == "get_config":
                        response = {
                            "type": "config_info",
                            "product_config": config_manager.product_info,
                            "voice_config": config_manager.voice_config,
                            "voice_options": config_manager.get_voice_options_info()
                        }
                        client_socket.sendall(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                        return True

                    elif command.get("type") == "reload_config":
                        success = config_manager.reload_configs()
                        response = {
                            "type": "config_response",
                            "success": success,
                            "message": "配置重新加载成功" if success else "配置重新加载失败"
                        }
                        client_socket.sendall(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                        return True

                except json.JSONDecodeError:
                    pass

            # 简单文本命令
            if message.startswith("!live_config"):
                parts = message.split()
                if len(parts) >= 2:
                    if parts[1] == "reload":
                        success = config_manager.reload_configs()
                        response = f"配置重新加载{'成功' if success else '失败'}"
                    elif parts[1] == "info":
                        response = f"产品: {config_manager.product_info['product_name']}, 价格: {config_manager.product_info['price']}, 语音: {config_manager.voice_config['voice']}"
                    elif parts[1] == "voice" and len(parts) >= 3:
                        gender = parts[2]
                        success = config_manager.set_voice_gender(gender)
                        response = f"语音切换为{gender} {'成功' if success else '失败'}"
                    else:
                        response = "可用命令: !live_config reload, !live_config info, !live_config voice [female/male/default]"
                else:
                    response = "配置命令格式: !live_config [reload/info/voice]"

                client_socket.sendall(response.encode('utf-8'))
                return True

        except Exception as e:
            print(f"❌ 处理配置命令时出错: {e}")

        return False

    def process_and_respond(self, client_socket, message):
        """处理消息并生成回复"""
        try:
            # 重新加载最新配置以确保实时性
            config_manager.reload_configs()

            response_text = self.process_message(message)
            audio_file = self.generate_audio(response_text)

            if audio_file and os.path.exists(audio_file):
                print(f"🎵 正在播放音频：{audio_file}")
                try:
                    # 使用跨平台音频播放器
                    play_audio_async(audio_file, delete_after=True)
                    print("✅ 音频播放任务已启动")

                except Exception as e:
                    print(f"❌ 播放失败: {e}")
                    # 即使播放失败也尝试删除文件
                    try:
                        os.remove(audio_file)
                        print(f"🗑️ 已删除音频文件：{audio_file}")
                    except Exception as delete_error:
                        print(f"⚠️ 删除音频文件失败: {delete_error}")

            response = json.dumps({
                "type": "message_response",
                "text": response_text,
                "audio": audio_file,
                "voice_used": config_manager.get_current_voice()
            }, ensure_ascii=False)

            try:
                client_socket.sendall(response.encode('utf-8'))
            except Exception as e:
                print(f"❌ 发送回复失败: {e}")

        except Exception as e:
            print(f"❌ 处理和回复消息时出错: {e}")

    def process_message(self, message):
        """根据内容决定优先回复还是调用Qwen，委托给AIService处理"""
        return ai_service.process_message(message)

    def build_prompt(self, message):
        """构建提示词，委托给AIService处理"""
        return ai_service.build_prompt(message)

    def generate_with_qwen(self, prompt):
        """调用Qwen生成回复，委托给AIService处理"""
        return ai_service.generate_with_qwen(prompt)

    def generate_audio(self, text):
        """生成语音音频，委托给AudioService处理"""
        return audio_service.generate_audio(text)

    def stop(self):
        """停止服务器"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print("🛑 Socket服务器已停止")


# ================== 增强的测试客户端 ==================
class TestClient:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port

    def send_message(self, message):
        """发送测试消息"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.host, self.port))

            client_socket.sendall(message.encode('utf-8'))

            # 接收回复
            response = client_socket.recv(4096)
            response_data = json.loads(response.decode('utf-8'))

            print(f"📤 发送: {message}")
            print(f"📥 回复: {response_data}")

            client_socket.close()
            return response_data

        except Exception as e:
            print(f"❌ 客户端发送消息失败: {e}")
            return None

    def update_product_config(self, config_data):
        """更新产品配置"""
        command = {
            "type": "update_product",
            "data": config_data
        }
        return self.send_message(json.dumps(command))

    def update_voice_config(self, config_data):
        """更新语音配置"""
        command = {
            "type": "update_voice",
            "data": config_data
        }
        return self.send_message(json.dumps(command))

    def get_config(self):
        """获取当前配置"""
        command = {"type": "get_config"}
        return self.send_message(json.dumps(command))

    def reload_config(self):
        """重新加载配置"""
        command = {"type": "reload_config"}
        return self.send_message(json.dumps(command))


# ================== 主程序入口 ==================
if __name__ == "__main__":
    # 检查API Key是否设置
    if dashscope.api_key == "YOUR_API_KEY":
        print(Constants.ERROR_MESSAGES["api_key_missing"])
        print("获取方式：https://dashscope.console.aliyun.com/")
        exit(1)

    print("🚀 启动WebSocket客户端...")
    print(f"📁 配置文件目录: {CONFIG_DIR}")
    print(f"📦 产品配置文件: {PRODUCT_CONFIG_FILE}")
    print(f"🎵 语音配置文件: {VOICE_CONFIG_FILE}")

    # 创建WebSocket客户端（使用常量配置）
    client = WebSocketClient(
        host='10.211.55.3',
        port=Constants.DEFAULT_PORT,
        reply_probability=0.2,  # 随机回复概率降低到20%
        max_queue_size=8,  # 增加队列长度
        reply_interval=20  # 回复间隔20秒
    )


    # 可自定义降级策略参数（使用常量默认值）
    # client.no_message_timeout = Constants.NO_MESSAGE_TIMEOUT
    # client.auto_introduce_interval = Constants.AUTO_INTRODUCE_INTERVAL

    async def main():
        max_retries = 5
        retry_count = 0

        while retry_count < max_retries:
            try:
                print(f"🔌 正在连接到WebSocket服务器... (尝试 {retry_count + 1}/{max_retries})")
                success = await client.connect()

                if success:
                    print("✅ 连接成功！开始监听消息...")
                    print("📢 提示：如果90秒内没有弹幕，将自动触发AI产品介绍")
                    print("⏱️ 自动介绍间隔为120秒，避免过于频繁")
                    retry_count = 0  # 重置重试计数

                    # 保持连接，监听消息
                    while client.is_connected():
                        await asyncio.sleep(1)

                    # 连接断开了
                    print("⚠️ WebSocket连接已断开，准备重连...")
                    await asyncio.sleep(5)  # 等待5秒后重连
                else:
                    print(f"❌ 连接失败，{5}秒后重试...")
                    await asyncio.sleep(5)

                retry_count += 1

            except KeyboardInterrupt:
                print("\n🛑 正在断开连接...")
                await client.close()
                print("✅ 已断开连接")
                break
            except Exception as e:
                print(f"❌ 运行错误: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    print(f"⏳ {5}秒后重试...")
                    await asyncio.sleep(5)
                else:
                    print("❌ 达到最大重试次数，程序退出")
                    await client.close()
                    break


    # 运行WebSocket客户端
    asyncio.run(main())
