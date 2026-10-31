"""内置 Skill：修复文件系统（SOP 复合能力）。"""
from __future__ import annotations

from pe_agent.skills.base import Skill, SkillManifest, SkillStep


class RepairFilesystemSkill(Skill):
    manifest = SkillManifest(
        name="repair_filesystem",
        version="0.1.0",
        description="修复文件系统：挂载 → fsck 修复 → 卸载",
        params_schema={
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "待修复分区，如 /dev/sda1"},
                "fs_type": {"type": "string", "default": "auto"},
            },
            "required": ["device"],
        },
        risk_level="high",
        permission="admin",
        tags=["filesystem", "repair"],
    )
    steps = [
        SkillStep(tool="run_fsck", params={"device": "{device}", "fs_type": "auto"}),
    ]
