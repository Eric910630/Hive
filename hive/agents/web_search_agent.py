# hive/agents/web_search_agent.py (v1.2 - Final Fix)

import logging
import json
from datetime import datetime
from typing import Dict, Any

# --- 【核心修正】: 根据官方最新文档，直接从包顶层导入正确的类名 TavilySearch ---
from langchain_tavily import TavilySearch

from hive.agents.base import BaseAgent, AgentManifest
from hive.core.memory import CoreMemory
from hive.utils.config import config

logger = logging.getLogger(__name__)

class WebSearchAgent(BaseAgent):
    """
    L2专家 - 网络探索者, 代号Seeker。
    已升级为使用Tavily搜索引擎，可以直接针对问题进行深入的网页信息整合和回答。
    """
    manifest = AgentManifest(
        name="WebSearchAgent",
        display_name="Seeker",
        description="使用Tavily搜索引擎在互联网上搜索实时信息，并返回可以直接回答问题的摘要。",
        parameters_json_schema={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "你想要搜索或需要回答的问题。"}},
            "required": ["query"]
        }
    )

    def __init__(self, memory: CoreMemory):
        super().__init__(memory)
        if not config.tavily_api_key:
            raise ValueError("Tavily API Key (TAVILY_API_KEY) 未在 .env 文件中配置。Seeker Agent无法初始化。")
        
        # --- 【核心修正】: 使用正确的类名 TavilySearch 进行实例化 ---
        self.search_tool = TavilySearch(max_results=5, tavily_api_key=config.tavily_api_key)

    def invoke(self, query: str, **kwargs) -> str:
        """
        执行网络搜索的核心方法。现在直接返回Tavily处理后的答案。
        """
        session_id = kwargs.get("session_id", "default_session")
        start_time = datetime.now()
        status = "FAILURE"
        output_data = {}
        error_message = None

        try:
            if not isinstance(query, str) or not query.strip():
                raise ValueError("参数 'query' 必须是一个非空的字符串。")
            
            logger.info(f"Seeker (Tavily) 正在研究问题: '{query}'")
            
            # TavilySearch工具的返回结果已经是精炼过的，可以直接使用
            raw_results = self.search_tool.invoke(query)
            
            output_data = {"answer": raw_results}
            status = "SUCCESS"

        except Exception as e:
            logger.error(f"Seeker (Tavily) 在研究 '{query}' 时失败: {e}", exc_info=True)
            error_message = f"网络搜索时发生错误: {str(e)}"
            output_data = {"error": error_message}
        finally:
            end_time = datetime.now()
            self.memory.log_agent_invocation(
                session_id=session_id,
                agent_name=self.manifest.name,
                input_data={"query": query},
                output_data=output_data,
                status=status,
                start_time=start_time,
                end_time=end_time,
                error_message=error_message
            )
        
        return json.dumps(output_data, ensure_ascii=False)