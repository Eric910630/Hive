# hive/utils/env_manager.py

import os
from typing import Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class EnvManager:
    """
    环境变量管理器，负责安全地加载和管理API密钥等敏感配置。
    """
    
    def __init__(self, env_file: str = ".env"):
        """
        初始化环境变量管理器。
        
        Args:
            env_file: .env文件路径，默认为项目根目录的.env文件
        """
        self.env_file = env_file
        self._load_env()
    
    def _load_env(self):
        """加载环境变量文件"""
        try:
            # 尝试加载.env文件
            if os.path.exists(self.env_file):
                load_dotenv(self.env_file)
                logger.info(f"成功加载环境变量文件: {self.env_file}")
            else:
                logger.warning(f"环境变量文件不存在: {self.env_file}")
                logger.info("请复制 env_template.txt 到 .env 并配置你的API密钥")
        except Exception as e:
            logger.error(f"加载环境变量文件失败: {e}")
    
    def get_deepseek_api_key(self) -> Optional[str]:
        """获取DeepSeek API密钥"""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key or api_key == "your_deepseek_api_key_here":
            logger.warning("DeepSeek API密钥未配置或使用默认值")
            return None
        return api_key
    
    def get_deepseek_model_name(self) -> str:
        """获取DeepSeek模型名称，默认为deepseek-chat"""
        return os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")
    
    def get_deepseek_base_url(self) -> str:
        """获取DeepSeek API基础URL"""
        return os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    def is_debug_enabled(self) -> bool:
        """检查是否启用调试模式"""
        return os.getenv("DEBUG", "false").lower() == "true"
    
    def get_db_path(self) -> Optional[str]:
        """获取数据库路径（可选配置）"""
        return os.getenv("HIVE_DB_PATH")
    
    def validate_config(self) -> bool:
        """
        验证配置是否完整。
        
        Returns:
            bool: 配置是否有效
        """
        api_key = self.get_deepseek_api_key()
        if not api_key:
            logger.error("DeepSeek API密钥未配置")
            return False
        
        logger.info("环境配置验证通过")
        return True
    
    def print_config_status(self):
        """打印配置状态（不显示敏感信息）"""
        print("🔧 Hive环境配置状态:")
        print(f"  📁 环境文件: {self.env_file}")
        print(f"  🔑 API密钥: {'✅ 已配置' if self.get_deepseek_api_key() else '❌ 未配置'}")
        print(f"  🤖 模型名称: {self.get_deepseek_model_name()}")
        print(f"  🌐 API地址: {self.get_deepseek_base_url()}")
        print(f"  🐛 调试模式: {'开启' if self.is_debug_enabled() else '关闭'}")
        
        if not self.get_deepseek_api_key():
            print("\n⚠️  配置提示:")
            print("   1. 复制 env_template.txt 到 .env")
            print("   2. 在 .env 中设置你的 DEEPSEEK_API_KEY")
            print("   3. 获取API密钥: https://platform.deepseek.com/")

if __name__ == "__main__":
    # 自测试
    print("🧪 测试环境变量管理器...")
    
    env_manager = EnvManager()
    env_manager.print_config_status()
    
    if env_manager.validate_config():
        print("✅ 配置验证通过")
    else:
        print("❌ 配置验证失败") 