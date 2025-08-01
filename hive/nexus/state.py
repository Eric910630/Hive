# hive/planning/state.py

from typing import TypedDict, List, Optional
from hive.interaction.alpha_engine import ParsedIntent

class HiveState(TypedDict):
    """
    定义了在LangGraph中流转的核心状态。
    它就像一个公文包，在所有节点之间传递。
    """
    user_query: str                  # 用户的原始输入
    intent: Optional[ParsedIntent]   # Alpha引擎解析出的意图
    
    # 我们用一个列表来追踪每一步的执行结果
    execution_history: List[dict]
    
    # 最终给用户的回复
    final_response: str 