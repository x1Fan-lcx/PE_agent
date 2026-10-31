"""冒烟测试：验证 Agent Loop 端到端可跑通（使用离线 FakeLLM）。"""
from __future__ import annotations

from pe_agent.graph.agent_loop import RepairAgent


def test_agent_loop_runs_without_api_key():
    agent = RepairAgent()
    result = agent.run("电脑开机进入 grub rescue 界面，无法启动系统")
    # FakeLLM 至少应产出轨迹，且不会无限循环
    assert "trajectory" in result
    assert len(result["trajectory"]) > 0
    # 步数受限，最多 max_iterations 步内终止
    assert len(result["trajectory"]) <= 6


def test_agent_returns_finished_flag():
    agent = RepairAgent()
    result = agent.run("系统启动卡住，日志报 EXT4-fs error")
    assert isinstance(result["finished"], bool)
