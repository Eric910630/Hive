# hive/utils/llm_factory.py

import logging
from typing import Dict
from langchain_core.language_models import BaseChatModel

# 导入所有需要支持的LLM的具体类
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama

# 导入我们的中央配置
from hive.utils.config import config

logger = logging.getLogger(__name__)

# 一个简单的内存缓存，用于存储已创建的LLM实例，避免重复创建
# 这在单次请求的生命周期内能提高效率
_llm_cache: Dict[str, BaseChatModel] = {}

def get_llm(tier: str) -> BaseChatModel:
    """
    LLM工厂函数，根据指定的层级（tier）创建并返回一个LLM实例。
    这是Hive系统中获取LLM的唯一、标准化的入口。
    
    Args:
        tier: 需求的LLM层级，可选值为 "heavyweight" 或 "lightweight"。

    Returns:
        一个实现了BaseChatModel接口的LLM实例。
    """
    # 确定用于缓存和查找配置的键
    # 对于"lightweight"，实际的提供商由config中的开关决定
    lookup_key = tier
    if tier == "lightweight":
        lookup_key = config.default_lightweight_tier
    
    # 1. 检查缓存
    if lookup_key in _llm_cache:
        logger.debug(f"LLM Factory: Returning cached instance for key '{lookup_key}'.")
        return _llm_cache[lookup_key]

    # 2. 获取配置
    llm_config = config.llms.get(lookup_key)
    if not llm_config:
        raise ValueError(f"LLM configuration for tier '{tier}' (resolved to key '{lookup_key}') not found in config.llms.")

    # 3. 根据配置创建新实例
    provider = llm_config.get("provider")
    llm_instance = None
    logger.info(f"LLM Factory: Creating new instance for provider '{provider}' with key '{lookup_key}'.")

    try:
        if provider == "deepseek":
            llm_instance = ChatDeepSeek(
                model=llm_config["model"],
                api_key=llm_config["api_key"],
                temperature=0  # Agent任务通常需要更确定的输出
            )
        elif provider == "openai":
            llm_instance = ChatOpenAI(
                model=llm_config["model"],
                api_key=llm_config["api_key"],
                temperature=0
            )
        elif provider == "ollama":
            llm_instance = ChatOllama(
                model=llm_config["model"],
                base_url=llm_config["base_url"],
                temperature=0
            )
        else:
            raise NotImplementedError(f"LLM provider '{provider}' is not supported by the factory.")
        
        # 4. 存入缓存并返回
        logger.info(f"LLM instance for key '{lookup_key}' created successfully.")
        _llm_cache[lookup_key] = llm_instance
        return llm_instance

    except KeyError as e:
        logger.error(f"Configuration error for provider '{provider}': Missing key {e}")
        raise ValueError(f"Missing configuration for provider '{provider}'. Check your .env and config.py.")
    except Exception as e:
        logger.error(f"Failed to create LLM instance for provider '{provider}': {e}", exc_info=True)
        raise