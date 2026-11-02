"""冒烟测试：验证 Agent Loop 端到端可跑通（强制使用离线 FakeLLM，不依赖真实 API）。"""
from __future__ import annotations

from pe_agent.core.llm import FakeChatModel
from pe_agent.graph.agent_loop import RepairAgent


def test_agent_loop_runs_without_api_key():
    agent = RepairAgent(llm=FakeChatModel())
    result = agent.run("电脑开机进入 grub rescue 界面，无法启动系统")
    # FakeLLM 至少应产出轨迹，且不会无限循环
    assert "trajectory" in result
    assert len(result["trajectory"]) > 0
    # 步数受限，最多 max_iterations 步内终止
    assert len(result["trajectory"]) <= 6


def test_agent_returns_finished_flag():
    agent = RepairAgent(llm=FakeChatModel())
    result = agent.run("系统启动卡住，日志报 EXT4-fs error")
    assert isinstance(result["finished"], bool)


def test_tool_missing_params_handled_gracefully():
    """真实模型会漏参，工具层应校验并回喂错误，而非崩溃。"""
    from pe_agent.tools import get_tool
    tool = get_tool("mount_partition")
    assert tool is not None
    missing = tool.validate_params({"mount_point": "/mnt"})
    assert "device" in missing
