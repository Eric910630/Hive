# hive/interaction/alpha_engine.py

import json
import logging
from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_deepseek import ChatDeepSeek
from hive.utils.config import config
from hive.utils.datetime_util import get_current_timestamp

logger = logging.getLogger(__name__)

class AgentTask(BaseModel):
    agent_name: Optional[str] = Field(description="目标Agent的名称。如果无法处理，则此字段必须为null。")
    operation: Optional[str] = Field(description="要执行的操作。如果无法处理，则为null。")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="操作所需参数。")

class ParsedIntent(BaseModel):
    user_query: str = Field(..., description="用户的原始自然语言指令。")
    task: AgentTask = Field(..., description="根据用户指令生成的Agent任务。")
    thought: str = Field(..., description="AI模型的思考过程，解释决策原因。")


class AlphaEngine:
    def __init__(self):
        if not config.deepseek_api_key:
            raise ValueError("DeepSeek API Key未配置。")
        self.llm = ChatDeepSeek(model="deepseek-chat", temperature=0, api_key=config.deepseek_api_key).with_structured_output(ParsedIntent)
        # Prompt不再是静态的，而是在调用时动态构建
    
    def _build_prompt(self) -> ChatPromptTemplate:
        # 注入时间上下文
        current_time = get_current_timestamp()
        
        system_prompt = f"""你是一个顶级的AI任务规划师，在Hive操作系统中担任Alpha引擎。
你的核心职责是：接收用户的自然语言指令，并将其转换成一个精确的、结构化的JSON任务对象。

**# 背景信息**
- **当前时间:** {current_time}

**# 可用工具 (Agents)**
1.  **Agent名称:** `FileSystemAgent`
    - **功能描述:** 用于执行本地文件系统的操作。
    - **支持的操作:** `list_directory`, `read_file`, `write_file`
2.  **Agent名称:** `WebSearchAgent`
    - **功能描述:** 用于在互联网上搜索实时信息。
    - **支持的操作:** `search`
    - **参数:** `query` (必需, str): 你要搜索的内容。

**# 你的思考过程与规则**
1.  **分析意图:** 结合当前时间，理解用户想做什么。
2.  **选择工具:** 从可用工具中选择最合适的Agent。
3.  **判断可行性:**
    - **如果能用现有工具完成**，请填充`task`的所有字段。对于`WebSearchAgent`，将用户的核心问题作为`query`参数。
    - **如果无法完成**，`agent_name`和`operation`字段必须为`null`。
4.  **生成思考链和JSON。**
"""
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "用户指令: '{query}'")
        ])

    def parse_intent(self, user_query: str) -> ParsedIntent:
        logging.info(f"AlphaEngine正在解析用户指令: '{user_query}'")
        # 每次解析都重新构建prompt以获取最新时间
        prompt = self._build_prompt()
        chain = prompt | self.llm
        try:
            parsed_result = chain.invoke({"query": user_query})
            logging.info(f"AlphaEngine解析成功。思考过程: {parsed_result.thought}")
            return parsed_result
        except Exception as e:
            logging.error(f"AlphaEngine在调用LLM时发生错误: {e}")
            raise 