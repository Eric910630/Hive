# hive/agents/get_agent.py

import logging
import json
from datetime import datetime
from typing import Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser

from hive.agents.base import BaseAgent, AgentManifest
from hive.core.memory import CoreMemory
from hive.utils.llm_factory import get_llm

logger = logging.getLogger(__name__)

# 定义GetAgent输出的Pydantic模型，用于JsonOutputParser
class ExtractedData(BaseModel):
    data: Dict[str, Any] = Field(description="The extracted data, conforming to the user's requested schema.")

class GetAgent(BaseAgent):
    """
    L2专家 - 信息提取专家, 代号'Get'。
    负责从非结构化文本中，根据用户提供的JSON Schema，提取出结构化的数据。
    """
    manifest = AgentManifest(
        name="GetAgent",
        display_name="Get",
        description="从一段文本中提取结构化的JSON数据。你需要提供原始文本和描述所需数据结构的JSON Schema。",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "text_to_process": {
                    "type": "string",
                    "description": "需要从中提取信息的原始文本。"
                },
                "extraction_schema": {
                    "type": "object",
                    "description": "一个JSON Schema对象，用于描述你希望提取的数据的结构。"
                }
            },
            "required": ["text_to_process", "extraction_schema"]
        }
    )

    def __init__(self, memory: CoreMemory):
        super().__init__(memory)
        # 1. 初始化轻量级LLM
        self.llm = get_llm(tier="lightweight")
        
        # 2. 初始化JSON输出解析器
        self.parser = JsonOutputParser(pydantic_object=ExtractedData)
        
        # 3. 创建Prompt模板
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "你是一个精准的信息提取引擎。你的唯一任务是根据用户提供的JSON Schema，从给定的文本中提取信息。"
             "你必须严格按照指定的格式输出，不要添加任何额外的解释、评论或非JSON内容。"
             "如果文本中缺少某个字段的信息，请使用null作为该字段的值。\n{format_instructions}"),
            ("human", "请从以下文本中提取信息：\n---TEXT---\n{text}\n---END TEXT---\n"),
        ])
        
        # 4. 组装处理链
        self.chain = self.prompt | self.llm | self.parser

    def invoke(self, text_to_process: str, extraction_schema: Dict[str, Any], **kwargs) -> str:
        """
        执行信息提取任务的核心方法。
        """
        session_id = kwargs.get("session_id", "default_session")
        start_time = datetime.now()
        status = "FAILURE"
        output_data = {}
        error_message = None

        try:
            if not text_to_process or not extraction_schema:
                raise ValueError("参数 'text_to_process' 和 'extraction_schema' 是必需的。")
            
            logger.info(f"GetAgent 正在从文本中提取数据...")
            
            # 将用户提供的schema作为格式化指令的一部分
            # 这是告诉LLM我们想要的具体结构
            format_instructions = json.dumps(extraction_schema, indent=2)

            # 调用处理链
            response = self.chain.invoke({
                "text": text_to_process,
                "format_instructions": format_instructions
            })
            
            output_data = response
            status = "SUCCESS"

        except Exception as e:
            logger.error(f"GetAgent 在提取数据时失败: {e}", exc_info=True)
            error_message = f"提取数据时发生错误: {str(e)}."
            output_data = {"error": error_message}
        finally:
            end_time = datetime.now()
            self.memory.log_agent_invocation(
                session_id=session_id,
                agent_name=self.manifest.name,
                input_data={"text_length": len(text_to_process), "schema": extraction_schema},
                output_data=output_data,
                status=status,
                start_time=start_time,
                end_time=end_time,
                error_message=error_message
            )
        
        # 为了工具调用的兼容性，最终返回一个JSON字符串
        return json.dumps(output_data, ensure_ascii=False)