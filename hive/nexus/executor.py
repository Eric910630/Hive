# hive/nexus/executor.py

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, END
import logging
from typing import Annotated, Sequence, TypedDict, Dict, Any

from hive.agents.file_system_agent import FileSystemAgent
from hive.agents.web_search_agent import WebSearchAgent
from hive.agents.calculator_agent import CalculatorAgent
from hive.agents.get_agent import GetAgent
from hive.core.memory import CoreMemory
from hive.utils.llm_factory import get_llm
# --- 【核心修改】: 导入我们的中央配置 ---
from hive.utils.config import config
# ------------------------------------

logger = logging.getLogger(__name__)

# 工具定义和封装 (无变动)
memory = CoreMemory()
fs_agent = FileSystemAgent(memory)
web_agent = WebSearchAgent(memory)
calc_agent = CalculatorAgent(memory)
get_agent = GetAgent(memory)

@tool
def seeker(query: str) -> str:
    """网络研究员: 使用Tavily搜索引擎直接研究和回答问题。能直接返回对问题的简洁回答或摘要，非常适合需要实时信息的问题。"""
    return web_agent.invoke(query=query)

@tool
def steward(operation: str, parameters: dict) -> str:
    """文件管家: 用于在本地计算机上进行文件操作（读、写、列出目录）。"""
    return fs_agent.invoke(operation=operation, parameters=parameters)

@tool
def abacus(expression: str) -> str:
    """计算专家: 用于执行精确的数学计算，能自动处理'万'、'亿'等单位。"""
    return calc_agent.invoke(expression=expression)

@tool
def get(text_to_process: str, extraction_schema: Dict[str, Any]) -> str:
    """信息提取专家: 从一段文本中，根据一个JSON Schema定义，提取出结构化的JSON数据。非常适合从Seeker返回的冗长文本中提取关键信息。"""
    return get_agent.invoke(text_to_process=text_to_process, extraction_schema=extraction_schema)

tools = [seeker, steward, abacus, get]

# 动态Prompt构建函数 (无变动)
def build_nexus_prompt() -> ChatPromptTemplate:
    tool_catalog_parts = []
    for t in tools:
        tool_catalog_parts.append(f"<tool><name>{t.name}</name><description>{t.description}</description></tool>")
    tool_catalog = "\n".join(tool_catalog_parts)

    prompt_template = f"""<mission_directive>
你的唯一、最终、不可逾越的核心使命是：生成一段面向用户的、有帮助的文本回复。工具调用只是你为了达成此目标而使用的中间过程，而不是目标本身。
</mission_directive>
<role_definition>
你是一个名为Nexus的、严谨、逻辑清晰的AI调度核心。你的角色不仅仅是工具的调用者，更是最终的分析师和决策者。
</role_definition>
<tools_catalog>
{tool_catalog}
</tools_catalog>
<rules_of_engagement>
1.  **【规划】** 你的首要任务是理解用户意图，并规划出获取必要信息的工具调用路径。
2.  **【信息收集】** 按需调用工具。当你使用`seeker`获取到大段文本后，你应该立即考虑使用`get`工具从中提取出你需要的、结构化的关键数据，而不是直接处理原始文本。这能极大提高你的工作效率。
3.  **【【【最终授权：切换为分析师角色（最重要）】】】** 在你收集完所有必要信息后，你【必须】停止调用任何工具。此时，你的角色从“调度员”切换为“分析师”。你【必须】利用你自身强大的语言理解和逻辑推理能力，对所有工具返回的数据进行全面的分析、计算、比较和总结，以直接、完整地回答用户的原始问题。**你的大脑，是你最终、也是最强大的工具。**
4.  **【优雅失败】** 如果你在**分析阶段**，发现即使有了所有数据，你依然无法完成用户的某个特定请求（例如进行复杂的数学建模），那么你的最终回复就应该是对这一事实的诚实报告，同时提供你已经成功分析出的部分结果。
5.  **【【【终极原则：使命必达】】】** 你的【唯一】且【最后】的动作，【必须】是生成一段完整的、总结性的回复给用户，这段回复是你作为“分析师”的最终成果。如果任务包含写文件，最终回复中必须包含对此操作的确认。**严禁在没有产出最终分析报告的情况下静默退出。**
</rules_of_engagement>"""

    return ChatPromptTemplate.from_messages([
        ("system", prompt_template),
        MessagesPlaceholder(variable_name="messages")
    ])

# Graph状态定义 (无变动)
class AgentState(TypedDict):
    messages: Annotated[Sequence[HumanMessage | AIMessage | ToolMessage], lambda x, y: x + y]

# 核心节点定义
async def agent_node(state: AgentState):
    prompt = build_nexus_prompt()
    llm = get_llm(tier="heavyweight")
    llm_with_tools = llm.bind_tools(tools)
    chain = prompt | llm_with_tools
    response = await chain.ainvoke({"messages": state["messages"]})
    return {"messages": [response]}

def execute_tools_node(state: AgentState):
    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {"messages": []}
    tool_calls = last_message.tool_calls
    tool_messages = []
    for tool_call in tool_calls:
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})
        tool_id = tool_call.get("id")
        selected_tool = next((t for t in tools if t.name == tool_name), None)
        if not selected_tool:
            output = f"错误: 未找到名为 '{tool_name}' 的工具。"
        else:
            try:
                output = selected_tool.invoke(**tool_args)
            except Exception as e:
                logger.error(f"工具执行失败! 工具: {tool_name}, 参数: {tool_args}", exc_info=True)
                output = f"执行工具 {tool_name} 时发生错误: {e}"
        tool_messages.append(ToolMessage(content=str(output), tool_call_id=tool_id))
    return {"messages": tool_messages}

async def reflect_node(state: AgentState):
    # --- 【核心修改】: 移除硬编码，使用config中的配置 ---
    last_message = state["messages"][-1]
    if not isinstance(last_message, ToolMessage):
        return {"messages": []}
    
    tool_output = last_message.content
    # 从中央配置读取阈值
    if len(tool_output) > config.reflector_max_text_length:
        logger.warning(f"检测到超长工具输出 ({len(tool_output)} chars)，超过阈值 {config.reflector_max_text_length}，启动信息精炼流程...")
        # ---------------------------------------------------
        tool_call_id = last_message.tool_call_id
        ai_message_with_call = next((msg for msg in reversed(state["messages"]) if isinstance(msg, AIMessage) and msg.tool_calls and any(tc.get("id") == tool_call_id for tc in msg.tool_calls)), None)
        original_query = "用户原始请求"
        if ai_message_with_call:
            tool_call = next((tc for tc in ai_message_with_call.tool_calls if tc.get("id") == tool_call_id), None)
            if tool_call:
                original_query = tool_call.get("args", {}).get("query", original_query)

        summarization_template = (
            "你是一个数据分析助理。你的任务是阅读一段长文本，并根据用户的原始问题，提取出最核心、最相关的信息。"
            "你的输出必须简洁、只包含关键数据点，并忽略所有无关内容。\n\n"
            "原始问题: '{query}'\n\n"
            "请总结以下长文本:\n\n---\n{long_text}\n---"
        )
        summarization_prompt = ChatPromptTemplate.from_template(summarization_template)
        summarizer_llm = get_llm(tier="lightweight")
        chain = summarization_prompt | summarizer_llm
        try:
            summary_response = await chain.ainvoke({
                "query": original_query,
                "long_text": tool_output[:config.reflector_max_text_length] + "..."
            })
            refined_content = summary_response.content
            logger.info(f"信息精炼成功，原文长度 {len(tool_output)}，摘要长度 {len(refined_content)}")
            new_tool_message = ToolMessage(content=refined_content, tool_call_id=tool_call_id)
            return {"messages": state["messages"][:-1] + [new_tool_message]}
        except Exception as e:
            logger.error("信息精炼过程中发生错误!", exc_info=True)
            error_message = ToolMessage(content=f"错误：工具返回信息过长，且在尝试总结时失败: {e}", tool_call_id=tool_call_id)
            return {"messages": state["messages"][:-1] + [error_message]}
            
    return {"messages": []}

def router_node(state: AgentState):
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "execute_tools"
    else:
        return END

def build_nexus_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("execute_tools", execute_tools_node)
    workflow.add_node("reflect", reflect_node)
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", router_node, {"execute_tools": "execute_tools", END: END})
    workflow.add_edge("execute_tools", "reflect")
    workflow.add_edge("reflect", "agent")
    graph = workflow.compile()
    print("✅ Hive Nexus Graph v1.7 (Dynamic Prompt & Configurable) has been successfully compiled.")
    return graph

nexus_graph = build_nexus_graph()