"""Skill 运行器：负责安全地执行一个 Skill。

执行链路（对齐 A.I.G 的「先检查、再执行、后审计」）：
  pre-check（权限 + 风险 + 输入护栏）→ 逐步调用工具（每步走工具护栏）
  → 记录审计 → 返回结果。

面试考点：为什么 Skill 不能直接跑，必须经过 runtime？——
因为 Skill 可能是动态创建/第三方来源的，runtime 是「能力」与「系统」之间唯一的受控通道。
"""
from __future__ import annotations

import re
from typing import Any

from pe_agent.security.guard import AgentGuard
from pe_agent.skills.base import Skill, SkillContext, SkillResult
from pe_agent.tools import get_tool


def _resolve_params(step_params: dict[str, Any],
                    skill_params: dict[str, Any]) -> dict[str, Any]:
    """把步骤里的 {param_name} 占位符替换为技能入参的实际值。"""
    resolved: dict[str, Any] = {}
    for k, v in step_params.items():
        if isinstance(v, str):
            resolved[k] = re.sub(
                r"\{(\w+)\}",
                lambda m: str(skill_params.get(m.group(1), m.group(0))),
                v,
            )
        else:
            resolved[k] = v
    return resolved


class SkillRuntime:
    def __init__(self, guard: AgentGuard | None = None) -> None:
        self._guard = guard or AgentGuard()

    def execute(self, skill: Skill, params: dict[str, Any],
                context: SkillContext | None = None) -> SkillResult:
        ctx = context or SkillContext()

        # 1) 输入护栏
        decision = self._guard.check_input(str(params))
        if not decision.allowed:
            return SkillResult(success=False, message=f"输入被拦截: {decision.reason}")

        # 2) 声明式步骤执行
        results: list[dict[str, Any]] = []
        if skill.steps:
            for step in skill.steps:
                tool = get_tool(step.tool)
                if tool is None:
                    return SkillResult(success=False, message=f"未知工具: {step.tool}")
                step_params = _resolve_params(step.params, params)
                missing = tool.validate_params(step_params)
                if missing:
                    return SkillResult(
                        success=False, message=f"步骤 {step.tool} 参数缺失: {', '.join(missing)}"
                    )
                guard_dec = self._guard.check_tool_call(
                    step.tool, step_params, tool.risk_level
                )
                if not guard_dec.allowed:
                    return SkillResult(
                        success=False, message=f"工具 {step.tool} 被拦截: {guard_dec.reason}"
                    )
                try:
                    res = tool.run(**step_params)
                except Exception as e:
                    return SkillResult(
                        success=False, message=f"步骤 {step.tool} 执行异常: {e}",
                        data={"audit": ctx.audit},
                    )
                ctx.audit.append(
                    {"tool": step.tool, "params": step_params,
                     "success": res.success, "message": res.message}
                )
                self._guard.audit(
                    {"trace_id": ctx.trace_id, "skill": skill.manifest.name,
                     "tool": step.tool, "allowed": True}
                )
                if not res.success:
                    return SkillResult(
                        success=False, message=f"步骤 {step.tool} 失败: {res.message}",
                        data={"results": results, "audit": ctx.audit},
                    )
                results.append({"tool": step.tool, "result": res.message})
            return SkillResult(
                success=True,
                message=f"技能 {skill.manifest.name} 执行完成",
                data={"results": results, "audit": ctx.audit},
            )

        # 3) 命令式（子类自定义 run）
        result = skill.run(params, ctx)
        result.data["audit"] = ctx.audit
        return result
