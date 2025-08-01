# hive/agents/calculator_agent.py (Super-powered Version)

import logging
import numexpr
import re
import json
from datetime import datetime
from typing import Dict, Any, Union

from hive.agents.base import BaseAgent, AgentManifest
from hive.core.memory import CoreMemory

logger = logging.getLogger(__name__)

class CalculatorAgent(BaseAgent):
    """
    L2专家 - 计算专家, 代号'Abacus'。
    经过强化的Abacus，现在能够直接处理包含常见单位和货币符号的数学表达式。
    """
    manifest = AgentManifest(
        name="CalculatorAgent",
        display_name="Abacus",
        description="用于执行精确的数学计算。可以直接处理包含数字、单位（万、亿、万亿）和货币符号的表达式。",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "一个需要计算的数学问题字符串，例如 '3.21万亿 * 0.05' 或 '($1,234.56 + ￥500) / 2'"
                }
            },
            "required": ["expression"]
        }
    )

    def _extract_and_clean_expression(self, text: str) -> str:
        """
        一个强大的内部方法，用于从文本中提取并清理出可供计算的纯数学表达式。
        【核心能力】
        1. 移除常见的货币符号和千位分隔符。
        2. 将中英文的数字单位转换为科学计数法。
        """
        # 移除货币符号（$, €, £, ¥）和逗号
        text = re.sub(r'[,\$€£¥元]', '', text)
        
        # 替换单位为科学计数法 (大小写不敏感)
        # 注意处理顺序，从大单位到小单位，防止"万亿"被先替换为"e6亿"
        text = re.sub(r'万亿\s*|\s*trillion', 'e12', text, flags=re.IGNORECASE)
        text = re.sub(r'亿\s*|\s*billion', 'e8', text, flags=re.IGNORECASE)
        text = re.sub(r'万\s*|\s*million', 'e4', text, flags=re.IGNORECASE) # 使用e4代表万
        
        # 提取所有数字（包括浮点数和科学计数法）和基本数学运算符
        # 这个正则表达式现在允许数字和运算符之间有空格
        parts = re.findall(r'\d+\.?\d*(?:e[+\-]?\d+)?|[\+\-\*\/\(\)\s]', text)
        
        if not parts:
            return ""
        
        # 将所有部分连接起来，并移除所有空格，形成一个紧凑的表达式
        cleaned_expression = "".join(parts).replace(" ", "")

        logger.info(f"表达式 '{text}' 被清理为 '{cleaned_expression}'")
        return cleaned_expression

    def invoke(self, expression: str, **kwargs) -> str:
        """
        执行计算任务的核心方法。
        """
        session_id = kwargs.get("session_id", "default_session")
        start_time = datetime.now()
        status = "FAILURE"
        output_data = {}
        error_message = None
        cleaned_expression = ""
        
        try:
            if not isinstance(expression, str):
                raise TypeError("输入参数 'expression' 必须是一个字符串。")
            
            logger.info(f"Abacus 接收到原始表达式: '{expression}'")
            
            cleaned_expression = self._extract_and_clean_expression(expression)
            
            if not cleaned_expression:
                raise ValueError("从输入中未能提取出有效的数学表达式。")
            
            # 使用numexpr进行安全的表达式计算
            result_val: Union[float, int] = numexpr.evaluate(cleaned_expression).item()
            output_data = {"result": float(result_val), "original_expression": expression}
            status = "SUCCESS"
            
        except Exception as e:
            logger.error(f"Abacus 在计算 '{expression}' 时失败: {e}", exc_info=True)
            error_message = f"计算错误: {str(e)}. 清理后的表达式为: '{cleaned_expression}'."
            output_data = {"error": error_message}
        finally:
            end_time = datetime.now()
            self.memory.log_agent_invocation(
                session_id=session_id,
                agent_name=self.manifest.name,
                input_data={"expression": expression},
                output_data=output_data,
                status=status,
                start_time=start_time,
                end_time=end_time,
                error_message=error_message
            )
        
        return json.dumps(output_data, ensure_ascii=False)