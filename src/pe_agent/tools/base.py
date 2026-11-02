"""工具基类：底层系统操作的统一封装（对应业界「MCP tool」这一层）。

面试考点：
- 为什么工具要声明 params_schema？—— 让 LLM 结构化传参、可校验、可做函数调用(function calling)。
- 为什么要标注 risk_level？—— 安全管控按风险分级拦截（见 security.guard）。
- 为什么用 dry_run？—— 开发/评测阶段避免真实改动系统，生产才放开。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["read_only", "low", "medium", "high"]


class ActionResult(BaseModel):
    """工具执行结果。"""

    success: bool = True
    message: str = ""
    data: dict[str, Any] = Field(default_factory=dict)


class Tool(ABC):
    """系统工具抽象基类。"""

    name: str = ""
    description: str = ""
    params_schema: dict[str, Any] = {}
    risk_level: RiskLevel = "read_only"

    @abstractmethod
    def run(self, **kwargs: Any) -> ActionResult:
        """执行工具。子类实现真实逻辑（初版为模拟实现）。"""

    def manifest(self) -> dict[str, Any]:
        """导出工具元信息，供 Agent prompt 注入与 MCP 注册。"""
        return {
            "name": self.name,
            "description": self.description,
            "params_schema": self.params_schema,
            "risk_level": self.risk_level,
        }

    def validate_params(self, params: dict[str, Any]) -> list[str]:
        """校验入参，返回缺失的必填字段列表（LLM 输出不可靠，工具层要容错）。"""
        required = self.params_schema.get("required", [])
        missing = []
        for r in required:
            v = params.get(r)
            if v is None or v == "":
                missing.append(r)
        return missing
