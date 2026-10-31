"""Skill 管理器：技能的生命周期（注册/卸载/启用/禁用/安全扫描）。

「创建」这一步对齐 2026 年 Agent 生态的「Skill 动态创建」方向——
允许用 manifest + 声明式步骤动态生成一个 Skill 类（框架雏形，不落盘可执行代码）。
「扫描」这一步对齐腾讯 A.I.G 的 Skill Scan（SkillTrustBench T01–T09）——
在技能上线前做静态安全体检，拦截危险命令、网络下载、exec 等风险。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from pe_agent.config import get_settings
from pe_agent.skills.base import (
    Skill,
    SkillContext,
    SkillManifest,
    SkillStep,
)


@dataclass
class ScanFinding:
    """安全扫描发现项。"""

    category: str
    severity: str  # low / medium / high / critical
    detail: str


@dataclass
class ScanReport:
    """安全扫描报告（对齐 A.I.G 的 T01–T09 风险分类）。"""

    findings: list[ScanFinding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(f.severity in ("high", "critical") for f in self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "findings": [{"category": f.category, "severity": f.severity,
                          "detail": f.detail} for f in self.findings],
        }


# 命令注入 / 危险操作模式（雏形；生产可接 aig-skill-scan）
_DANGEROUS_PATTERNS = [
    (re.compile(r"\brm\s+-rf\b"), "T01 危险命令", "high"),
    (re.compile(r"\bmkfs\b"), "T01 危险命令", "critical"),
    (re.compile(r"\bdd\s+if="), "T01 危险命令", "critical"),
    (re.compile(r"\beval\(|exec\(|subprocess\.|os\.system"), "T04 动态代码执行", "high"),
    (re.compile(r"(https?://|curl\s+|wget\s+)"), "T03 远程载荷下载", "medium"),
    (re.compile(r"\.\./|/etc/passwd|/etc/shadow"), "T02 越权访问", "medium"),
]


def scan_skill_source(source: str) -> ScanReport:
    """对技能「源码/描述+步骤」做静态安全扫描（A.I.G 风格，雏形）。"""
    report = ScanReport()
    for pattern, category, severity in _DANGEROUS_PATTERNS:
        if pattern.search(source):
            report.findings.append(
                ScanFinding(category=category, severity=severity, detail=pattern.pattern)
            )
    return report


class SkillManager:
    def __init__(self, registry: Any) -> None:
        self._registry = registry
        self._disabled: set[str] = set()

    def register(self, skill_cls: type[Skill]) -> None:
        """注册前先做安全扫描，高危直接拒绝。"""
        src = f"{skill_cls.manifest.description} {skill_cls.manifest.name}"
        report = scan_skill_source(src)
        if not report.passed:
            raise ValueError(f"Skill 未通过安全扫描: {report.to_dict()}")
        self._registry.register(skill_cls)

    def unregister(self, name: str) -> None:
        self._disabled.discard(name)

    def enable(self, name: str) -> None:
        self._disabled.discard(name)

    def disable(self, name: str) -> None:
        self._disabled.add(name)

    def is_enabled(self, name: str) -> bool:
        return name not in self._disabled

    def create_skill(
        self,
        name: str,
        description: str,
        steps: list[dict[str, Any]],
        risk_level: str = "medium",
        permission: str = "restricted",
    ) -> type[Skill]:
        """动态创建一个声明式 Skill（框架雏形）。

        参数 `steps` 形如 [{"tool": "mount_partition", "params": {...}}, ...]。
        生产环境中这一步应配合安全扫描 + 权限审批 + 版本管理。
        """
        manifest = SkillManifest(
            name=name,
            description=description,
            risk_level=risk_level,  # type: ignore[arg-type]
            permission=permission,  # type: ignore[arg-type]
        )
        parsed_steps = [SkillStep(tool=s["tool"], params=s.get("params", {})) for s in steps]

        # 扫描步骤里引用的工具名与参数（防命令注入）
        src = " ".join([s.tool for s in parsed_steps]) + " " + str(steps)
        report = scan_skill_source(src)
        if not report.passed:
            raise ValueError(f"Skill 未通过安全扫描: {report.to_dict()}")

        new_cls = type(
            name, (Skill,), {"manifest": manifest, "steps": parsed_steps}
        )
        self._registry.register(new_cls)
        return new_cls
