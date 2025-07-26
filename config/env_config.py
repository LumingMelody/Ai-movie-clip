"""
环境变量配置加载器
从 .env 文件加载配置，提供统一的配置访问接口
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class Config:
    """统一的配置类"""
    
    # AI Model API Keys
    DASHSCOPE_API_KEY: str = os.getenv('DASHSCOPE_API_KEY', '')
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    COZE_API_KEY: str = os.getenv('COZE_API_KEY', '')
    
    # OSS Configuration
    OSS_ACCESS_KEY_ID: str = os.getenv('OSS_ACCESS_KEY_ID', '')
    OSS_ACCESS_KEY_SECRET: str = os.getenv('OSS_ACCESS_KEY_SECRET', '')
    OSS_ENDPOINT: str = os.getenv('OSS_ENDPOINT', 'https://oss-cn-hangzhou.aliyuncs.com')
    OSS_BUCKET_NAME: str = os.getenv('OSS_BUCKET_NAME', '')
    
    # Aliyun Configuration
    ALIYUN_ACCESS_KEY_ID: str = os.getenv('ALIYUN_ACCESS_KEY_ID', '')
    ALIYUN_ACCESS_KEY_SECRET: str = os.getenv('ALIYUN_ACCESS_KEY_SECRET', '')
    
    # Database Configuration
    DATABASE_URL: str = os.getenv('DATABASE_URL', '')
    
    # Server Configuration
    SERVER_HOST: str = os.getenv('SERVER_HOST', '0.0.0.0')
    SERVER_PORT: int = int(os.getenv('SERVER_PORT', '8000'))
    
    # WebSocket Configuration
    WEBSOCKET_HOST: str = os.getenv('WEBSOCKET_HOST', '10.211.55.3')
    WEBSOCKET_PORT: int = int(os.getenv('WEBSOCKET_PORT', '8888'))
    
    # Feature Flags
    USE_VOICE_CLONING: bool = os.getenv('USE_VOICE_CLONING', 'false').lower() == 'true'
    ENABLE_AUTO_INTRODUCE: bool = os.getenv('ENABLE_AUTO_INTRODUCE', 'true').lower() == 'true'
    
    # Voice Configuration
    DEFAULT_VOICE_MODEL: str = os.getenv('DEFAULT_VOICE_MODEL', 'cosyvoice-v2')
    DEFAULT_VOICE_TYPE: str = os.getenv('DEFAULT_VOICE_TYPE', 'longxiaochun_v2')
    
    @classmethod
    def validate(cls) -> bool:
        """验证必要的配置是否存在"""
        required_keys = [
            'DASHSCOPE_API_KEY',
            'OSS_ACCESS_KEY_ID',
            'OSS_ACCESS_KEY_SECRET',
        ]
        
        missing_keys = []
        for key in required_keys:
            if not getattr(cls, key):
                missing_keys.append(key)
        
        if missing_keys:
            print(f"⚠️ 警告: 以下必要的环境变量未设置: {', '.join(missing_keys)}")
            print("请在 .env 文件中配置这些变量")
            return False
        
        return True
    
    @classmethod
    def get_oss_config(cls) -> dict:
        """获取OSS配置"""
        return {
            'access_key_id': cls.OSS_ACCESS_KEY_ID,
            'access_key_secret': cls.OSS_ACCESS_KEY_SECRET,
            'endpoint': cls.OSS_ENDPOINT,
            'bucket_name': cls.OSS_BUCKET_NAME,
        }
    
    @classmethod
    def get_dashscope_config(cls) -> dict:
        """获取DashScope配置"""
        return {
            'api_key': cls.DASHSCOPE_API_KEY,
        }

# 创建全局配置实例
config = Config()

# 验证配置
if not config.validate():
    print("⚠️ 某些功能可能无法正常工作，请检查环境配置")