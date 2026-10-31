"""Skill 框架测试：注册 / 管理 / 运行 / 安全扫描。"""
from __future__ import annotations

import pytest

from pe_agent.skills import build_default_skill_system
from pe_agent.skills.base import SkillContext
from pe_agent.skills.manager import scan_skill_source


def test_builtin_skills_registered():
    registry, _, _ = build_default_skill_system()
    assert registry.get("repair_boot") is not None
    assert registry.get("repair_filesystem") is not None


def test_repair_boot_skill_runs():
    registry, manager, runtime = build_default_skill_system()
    skill_cls = registry.get("repair_boot")
    assert skill_cls is not None
    ctx = SkillContext(dry_run=True, trace_id="t1")
    result = runtime.execute(skill_cls(), {"device": "/dev/sda", "root_device": "/dev/sda1"}, ctx)
    assert result.success, result.message
    assert result.data["audit"]


def test_dangerous_skill_rejected():
    _, manager, _ = build_default_skill_system()
    with pytest.raises(ValueError):
        manager.create_skill(
            name="bad_skill",
            description="删除所有数据",
            steps=[{"tool": "write_file", "params": {"path": "/etc", "content": "rm -rf /"}}],
        )


def test_scan_detects_dangerous_command():
    report = scan_skill_source("执行 rm -rf / 清空系统")
    assert not report.passed
    assert any(f.severity in ("high", "critical") for f in report.findings)
