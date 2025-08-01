# hive/agents/file_system_agent.py (Sanitized & Patched Version)

import os
import logging
import json
from datetime import datetime
from typing import Dict, Any

from hive.agents.base import BaseAgent, AgentManifest
from hive.core.memory import CoreMemory

logger = logging.getLogger(__name__)

class FileSystemAgent(BaseAgent):
    """L2专家 - 文件管家, 代号Steward"""
    manifest = AgentManifest(
        name="FileSystemAgent",
        display_name="Steward",
        description="用于操作本地文件，支持'read_file', 'write_file', 'list_directory'。",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "要执行的操作，可选值为 'read_file', 'write_file', 'list_directory'。",
                    "enum": ["read_file", "write_file", "list_directory"]
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "目标文件或目录的路径。为了安全，推荐使用相对路径。"},
                        "content": {"type": "string", "description": "当操作为 'write_file' 时，要写入的内容。"}
                    },
                    "required": ["path"]
                }
            },
            "required": ["operation", "parameters"]
        }
    )
    
    def invoke(self, operation: str, parameters: dict, **kwargs) -> str:
        """
        执行文件系统操作的核心方法。
        """
        session_id = kwargs.get("session_id", "default_session")
        path = parameters.get("path")
        
        if path:
            # 自动展开用户主目录符号 '~'
            path = os.path.expanduser(path)
        
        start_time = datetime.now()
        status = "FAILURE"
        error_message = None
        output_data = {}

        try:
            if not operation or not path:
                raise ValueError("参数 'operation' 和 'parameters.path' 是必需的。")

            logger.info(f"Steward 正在对路径 '{path}' 执行操作: '{operation}'")
            
            if operation == "list_directory":
                if not os.path.isdir(path):
                    raise FileNotFoundError(f"目录不存在: {path}")
                output_data = {"directory_listing": os.listdir(path)}
            elif operation == "read_file":
                if not os.path.isfile(path):
                    raise FileNotFoundError(f"文件不存在: {path}")
                with open(path, 'r', encoding='utf-8') as f:
                    output_data = {"file_content": f.read()}
            elif operation == "write_file":
                content = parameters.get("content", "")
                
                # --- 【核心Bug修复】 ---
                # 获取目录路径
                dir_path = os.path.dirname(path)
                
                # 仅当目录路径非空时才创建目录，这可以防止对当前目录进行无效的makedirs操作
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)
                # --- 修复结束 ---
                
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                output_data = {"write_status": "success", "path": path, "content_length": len(content)}
            else:
                raise ValueError(f"Steward不支持的操作: {operation}。有效操作为 'read_file', 'write_file', 'list_directory'。")
            
            status = "SUCCESS"

        except Exception as e:
            logger.error(f"Steward在操作 '{path}' 时失败: {e}", exc_info=True)
            error_message = str(e)
            output_data = {"error": error_message}
        finally:
            end_time = datetime.now()
            self.memory.log_agent_invocation(
                session_id=session_id,
                agent_name=self.manifest.name,
                input_data={"operation": operation, "parameters": parameters}, 
                output_data=output_data,
                status=status,
                start_time=start_time,
                end_time=end_time,
                error_message=error_message
            )
        
        return json.dumps(output_data, ensure_ascii=False)