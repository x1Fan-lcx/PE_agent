"""Skill 框架 —— 基类与元信息。

概念澄清（面试高频）：
- Tool = 原子能力（挂载、修引导），对应 MCP tool；
- Skill = 复合能力/SOP，把「一段指令 + 一串工具调用」打包成可复用、可版本化、可动态管理的单元。
  这正是 2026 年 Agent 生态里新的抽象层，也是新的攻击面（腾讯 A.I.G 专门做 Skill 扫描）。

框架雏形只做三件事：定义契约(manifest)、声明式步骤(steps)、可覆盖的执行(run)。
"""
from __future__ import annotations

from abc import ABC
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, Field

from pe_agent.tools.base import RiskLevel

Permission = Literal["public", "restricted", "admin"]


class SkillManifest(BaseModel):
    """技能的元信息（类比 npm 包的 package.json / MCP tool 的声明）。"""

    name: str
    version: str = "0.1.0"
    description: str = ""
    params_schema: dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel = "medium"
    permission: Permission = "restricted"
    tags: list[str] = Field(default_factory=list)


class SkillContext(BaseModel):
    """执行上下文：目标设备、是否 dry-run、调用链 trace_id（用于审计）。"""

    device: str | None = None
    dry_run: bool = True
    trace_id: str = ""
    # 调用链：记录 skill 内部触发了哪些工具，供安全审计/评测回放
    audit: list[dict[str, Any]] = Field(default_factory=list)


class SkillStep(BaseModel):
    """声明式步骤：调用一个工具并传参。"""

    tool: str
    params: dict[str, Any] = Field(default_factory=dict)


class SkillResult(BaseModel):
    success: bool = True
    message: str = ""
    data: dict[str, Any] = Field(default_factory=dict)


class Skill(ABC):
    """技能抽象基类。

    子类二选一：
    1) 声明式：只填 `manifest` 和 `steps`，由 runtime 按顺序调用工具；
    2) 命令式：覆盖 `run()` 自定义编排逻辑。
    """

    manifest: ClassVar[SkillManifest]
    steps: list[SkillStep] = []

    def run(self, params: dict[str, Any], context: SkillContext) -> SkillResult:
        """默认实现：按 steps 顺序调用工具（真正的编排在 runtime，这里留扩展点）。"""
        return SkillResult(success=False, message="未实现 run() 且无声明式 steps")
