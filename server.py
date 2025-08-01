# server.py (Now with Centralized Logging)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any

# 导入我们的配置和日志模块
from hive.utils.config import config
from hive.utils.logging_config import setup_logging
# --- 【核心修改】: 更新import路径 ---
from hive.nexus.executor import nexus_graph
# ------------------------------------
import uvicorn
import json
import logging

# --- 【核心改动】: 在应用的最开始就配置好日志系统 ---
setup_logging()
# --------------------------------------------------

# 获取一个logger实例，用于在本文件中记录日志
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hive Nexus Server v14.0 (Observable)",
    version="14.0",
)

# 动态CORS策略 (逻辑无变动)
if config.is_development:
    logger.info("CORS策略: [开发模式] 已启用，允许所有localhost来源。")
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://localhost:\d+",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    logger.info(f"CORS策略: [生产模式] 已启用，仅允许来源: {config.frontend_cors_origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.frontend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# API 端点 (逻辑无变动)
def safe_serialize(obj: Any) -> Any:
    """一个健壮的、通用的序列化函数，用于安全地将LangChain对象转换为JSON。"""
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode='json')
    if isinstance(obj, dict):
        return {k: safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [safe_serialize(i) for i in obj]
    return obj

@app.post("/nexus/stream_events")
async def stream_nexus_events(request: Request):
    """处理前端请求，并流式返回LangGraph执行过程中的所有事件。"""
    try:
        body = await request.json()
        graph_input = body.get("input", {})
        logger.info(f"接收到新的流式请求, 输入内容: {graph_input}")

        async def event_generator():
            logger.debug("--- [SERVER] 启动事件流传输... ---")
            async for event in nexus_graph.astream_events(graph_input, version="v2"):
                try:
                    safe_event = safe_serialize(event)
                    data_to_send = json.dumps(safe_event)
                    # 调试时，可以在这里打印事件来追踪流程
                    # logger.debug(f"发送事件: {data_to_send}")
                    yield f"data: {data_to_send}\n\n"
                except Exception as e:
                    logger.error("序列化事件时发生意外错误!", exc_info=True)
            logger.debug("--- [SERVER] 事件流传输完毕。 ---")
        
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        logger.error("流式端点发生严重错误!", exc_info=True)
        async def error_stream():
             error_event = { "event": "error", "data": str(e) }
             yield f"data: {json.dumps(error_event)}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream", status_code=500)

# 脚本主入口
if __name__ == "__main__":
    logger.info("--- 启动 Hive Nexus 服务器 ---")
    uvicorn.run(
        "server:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=config.is_development,
        log_config=None # 【重要】: 禁用uvicorn的默认日志配置，因为我们已经自己接管了
    )