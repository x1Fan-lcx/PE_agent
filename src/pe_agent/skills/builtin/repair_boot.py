"""内置 Skill：修复引导（SOP 复合能力）。

把麒麟「分级故障诊断状态机」里的一个分支，抽象成一个可复用、可版本化的 Skill。
步骤 = 查日志定位 → 挂载系统分区 → 重装引导 → 卸载收尾，是一个完整 SOP。
"""
from __future__ import annotations

from pe_agent.skills.base import Skill, SkillManifest, SkillStep


class RepairBootSkill(Skill):
    manifest = SkillManifest(
        name="repair_boot",
        version="0.1.0",
        description="修复系统引导：先查日志定位，再挂载分区重装 bootloader，最后卸载收尾",
        params_schema={
            "type": "object",
            "properties": {
                "device": {"type": "string"},
                "root_device": {"type": "string", "description": "根分区，如 /dev/sda1"},
            },
            "required": ["device", "root_device"],
        },
        risk_level="high",
        permission="admin",
        tags=["boot", "repair"],
    )
    steps = [
        SkillStep(tool="read_log", params={"keyword": "boot"}),
        SkillStep(tool="mount_partition", params={"device": "{root_device}", "mount_point": "/mnt/sysroot"}),
        SkillStep(tool="reinstall_bootloader", params={"device": "{device}", "method": "auto"}),
        SkillStep(tool="unmount_partition", params={"mount_point": "/mnt/sysroot"}),
    ]
