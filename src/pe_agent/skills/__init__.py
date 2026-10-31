"""Skill 框架子包。

对外暴露：契约(base) / 注册(registry) / 管理(manager) / 运行(runtime) 四大件，
以及一个「默认装配」的全局实例，供 Agent Loop 直接使用。
"""
from __future__ import annotations

from pe_agent.security.guard import AgentGuard
from pe_agent.skills.base import (
    Skill,
    SkillContext,
    SkillManifest,
    SkillResult,
    SkillStep,
)
from pe_agent.skills.builtin import RepairBootSkill, RepairFilesystemSkill
from pe_agent.skills.manager import (
    ScanReport,
    SkillManager,
    scan_skill_source,
)
from pe_agent.skills.registry import SkillRegistry
from pe_agent.skills.runtime import SkillRuntime


def build_default_skill_system() -> tuple[SkillRegistry, SkillManager, SkillRuntime]:
    """装配默认技能系统：注册内置技能，返回 (registry, manager, runtime)。"""
    registry = SkillRegistry()
    manager = SkillManager(registry)
    guard = AgentGuard()
    runtime = SkillRuntime(guard)
    for cls in (RepairBootSkill, RepairFilesystemSkill):
        manager.register(cls)
    return registry, manager, runtime


__all__ = [
    "Skill", "SkillManifest", "SkillContext", "SkillStep", "SkillResult",
    "SkillRegistry", "SkillManager", "SkillRuntime",
    "ScanReport", "scan_skill_source",
    "RepairBootSkill", "RepairFilesystemSkill",
    "build_default_skill_system",
]
