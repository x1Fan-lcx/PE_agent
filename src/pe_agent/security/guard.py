"""安全管控（AgentGuard）——对齐腾讯朱雀 A.I.G（AI-Infra-Guard）的防御思路。

A.I.G 是「红队/扫描」视角，本项目是「防御/落地」视角：把同一套风险认知
（工具投毒、命令注入、凭据泄露、提示注入、越权访问）落实为 Agent 运行时的三道闸：
  1) 输入闸 check_input   —— 提示注入检测
  2) 工具闸 check_tool_call —— 危险命令拦截 + 挂载白名单 + 风险分级 + dry-run 强制
  3) 输出闸 check_output  —— 敏感信息脱敏 / 越权结果拦截
外加全链路审计日志（audit），对应 Claw-Eval 强调的「执行过程可审计」。

落地位置：Agent Loop 的 Act 节点（执行前/后）、Skill Runtime（执行前）、API 层（入口/出口）。
"""
from __future__ import annotations

import re
import time
from typing import Any

from pydantic import BaseModel

from pe_agent.config import get_settings
from pe_agent.tools.base import RiskLevel


class GuardDecision(BaseModel):
    allowed: bool = True
    reason: str = ""
    severity: str = "none"  # none / low / medium / high / critical


# 提示注入特征（雏形；生产可用分类模型 / 更全的注入语料）
_INJECTION_PATTERNS = [
    re.compile(r"忽略(以上|之前|之前所有|系统).{0,8}(指令|提示|规则)", re.S),
    re.compile(r"ignore (all |any )?(previous|above|prior) (instructions|prompts)", re.I),
    re.compile(r"你现在(是|扮演|的身份)", re.S),
    re.compile(r"system\s*:", re.I),
    re.compile(r"泄露|打印|输出.{0,4}(系统提示词|system prompt|密钥|apikey)", re.I | re.S),
]

_RISK_ORDER: dict[RiskLevel, int] = {
    "read_only": 0, "low": 1, "medium": 2, "high": 3,
}


class AgentGuard:
    """Agent 运行时安全护栏。"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.audit_log: list[dict[str, Any]] = []

    # ---- 输入闸：提示注入检测 ----
    def check_input(self, text: str) -> GuardDecision:
        for pat in _INJECTION_PATTERNS:
            if pat.search(text):
                return GuardDecision(
                    allowed=False,
                    reason=f"检测到提示注入特征: {pat.pattern}",
                    severity="high",
                )
        return GuardDecision(allowed=True)

    # ---- 工具闸：危险命令 + 白名单 + 风险分级 + dry-run ----
    def check_tool_call(self, tool_name: str, params: dict[str, Any],
                        risk_level: RiskLevel = "read_only") -> GuardDecision:
        # 1) 命令注入 / 危险参数
        params_str = str(params)
        for cmd in self.settings.dangerous_commands:
            if cmd.lower() in params_str.lower():
                return GuardDecision(
                    allowed=False, reason=f"参数含危险命令: {cmd}", severity="critical"
                )
        # 2) 挂载白名单
        mp = params.get("mount_point")
        if mp and not any(str(mp).startswith(p) for p in self.settings.mount_whitelist):
            return GuardDecision(
                allowed=False, reason=f"挂载点 {mp} 不在白名单", severity="high"
            )
        # 3) 高风险操作在 dry-run 模式下强制只读模拟
        if self.settings.safety_dry_run and _RISK_ORDER[risk_level] >= _RISK_ORDER["high"]:
            # 不拦截，但标记为模拟执行（工具内部已按 dry_run 处理）
            return GuardDecision(allowed=True, reason="high-risk 操作进入 dry-run 模拟")
        return GuardDecision(allowed=True)

    # ---- 输出闸：敏感信息检测 ----
    def check_output(self, text: str) -> GuardDecision:
        if re.search(r"AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|-----BEGIN", text):
            return GuardDecision(
                allowed=False, reason="输出疑似包含敏感凭据", severity="critical"
            )
        return GuardDecision(allowed=True)

    # ---- 审计 ----
    def audit(self, event: dict[str, Any]) -> None:
        event["ts"] = time.time()
        self.audit_log.append(event)
