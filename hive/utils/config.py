# hive/utils/config.py

import os
from dotenv import load_dotenv
import logging
from typing import List, Dict, Any

class AppConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
            if os.path.exists(env_path):
                load_dotenv(dotenv_path=env_path)
                logging.info(f"成功从 {env_path} 加载配置。")
            else:
                logging.warning(f"警告: 未在 {env_path} 找到 .env 文件。将依赖系统环境变量。")
            
            cls._instance.app_env = os.getenv("APP_ENV", "development").lower()
            cls._instance.frontend_cors_origins_str = os.getenv("FRONTEND_CORS_ORIGINS", "")
            
            cls._instance.reflector_max_text_length = int(os.getenv("REFLECTOR_MAX_TEXT_LENGTH", "4000"))
            cls._instance.api_host = os.getenv("API_HOST", "http://localhost")
            cls._instance.api_port = int(os.getenv("API_PORT", "8000"))

            cls._instance.llms = {
                "heavyweight": {
                    "provider": "deepseek",
                    "model": os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat"),
                    "api_key": os.getenv("DEEPSEEK_API_KEY")
                },
                "lightweight_api": {
                    "provider": "openai",
                    "model": os.getenv("OPENAI_LIGHT_MODEL_NAME", "gpt-3.5-turbo"),
                    "api_key": os.getenv("OPENAI_API_KEY")
                },
                "lightweight_local": {
                    "provider": "ollama",
                    # --- 【最终确认】: 确保默认本地模型是llama2 ---
                    "model": os.getenv("OLLAMA_MODEL_NAME", "llama2"), 
                    # ----------------------------------------------
                    "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                }
            }
            
            cls._instance.default_lightweight_tier = "lightweight_local"
            
            cls._instance.tavily_api_key = os.getenv("TAVILY_API_KEY")

            cls._instance._validate_and_log()

        return cls._instance
        
    @property
    def api_base_url(self) -> str:
        return f"{self.api_host}:{self.api_port}"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def frontend_cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.frontend_cors_origins_str.split(',')] if self.frontend_cors_origins_str else []

    def _validate_and_log(self):
        logging.info(f"--- [Hive配置] 当前运行环境 (APP_ENV): {self.app_env.upper()} ---")
        
        logging.info(f"后端API服务地址 (API_HOST:API_PORT): {self.api_base_url}")
        logging.info(f"ReflectorNode 触发阈值 (REFLECTOR_MAX_TEXT_LENGTH): {self.reflector_max_text_length} chars")
        
        heavy_conf = self.llms["heavyweight"]
        if not heavy_conf.get("api_key"):
            logging.warning("DEEPSEEK_API_KEY (heavyweight LLM) 未设置！Nexus核心可能无法工作。")
        else:
            logging.info(f"✅ Heavyweight LLM (Nexus核心) 配置: Provider='{heavy_conf['provider']}', Model='{heavy_conf['model']}'")

        light_tier_key = self.default_lightweight_tier
        light_conf = self.llms.get(light_tier_key)
        
        if light_conf:
            logging.info(f"✅ Lightweight LLM (L2专家) 已切换至: [ {light_tier_key.upper()} ]")
            logging.info(f"   - Provider: '{light_conf['provider']}', Model: '{light_conf['model']}'")
            if light_tier_key == "lightweight_api" and not light_conf.get("api_key"):
                logging.warning(f"   - 警告: {light_tier_key.upper()} 模式下需要API密钥，但未在.env中配置！")
        else:
            logging.error(f"配置错误: default_lightweight_tier '{light_tier_key}' 未在llms配置中找到！")

        if not self.tavily_api_key:
            logging.warning("TAVILY_API_KEY 未设置！Seeker Agent将无法工作。")
        else:
            logging.info("✅ Tavily API Key 已配置。")

config = AppConfig()