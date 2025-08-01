# hive/agents/base.py
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import Any, Dict

from hive.core.memory import CoreMemory

class AgentManifest(BaseModel):
    name: str = Field(..., description="Agent的唯一内部名称，通常是类名。")
    display_name: str = Field(..., description="Agent的代号，用于向用户展示和在Prompt中引用。")
    description: str = Field(..., description="详细描述Agent的功能。")
    # 正式添加参数定义字段，并提供一个默认的空对象
    parameters_json_schema: Dict[str, Any] = Field(default_factory=dict, description="一个JSON Schema对象，定义了invoke方法需要的参数。")
    version: str = "1.0"

class BaseAgent(ABC):
    manifest: AgentManifest
    def __init__(self, memory: CoreMemory): self.memory = memory
    @abstractmethod
    def invoke(self, **kwargs: Any) -> Dict[str, Any]: pass
    def __repr__(self) -> str: return f"{self.__class__.__name__}(display_name='{self.manifest.display_name}')" 