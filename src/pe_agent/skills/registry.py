"""Skill 注册中心：name -> Skill 类 的映射，负责登记、查询、枚举。"""
from __future__ import annotations

from typing import Any

from pe_agent.skills.base import Skill


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, type[Skill]] = {}

    def register(self, skill_cls: type[Skill]) -> None:
        name = skill_cls.manifest.name
        if name in self._skills:
            raise ValueError(f"Skill 已存在: {name}")
        self._skills[name] = skill_cls

    def get(self, name: str) -> type[Skill] | None:
        return self._skills.get(name)

    def list(self) -> list[dict[str, Any]]:
        """导出所有已注册技能的元信息（供 Agent prompt 注入 / 管理接口展示）。"""
        return [
            {"name": m.name, "version": m.version, "description": m.description,
             "risk_level": m.risk_level, "permission": m.permission, "tags": m.tags}
            for m in (c.manifest for c in self._skills.values())
        ]

    def __len__(self) -> int:
        return len(self._skills)
