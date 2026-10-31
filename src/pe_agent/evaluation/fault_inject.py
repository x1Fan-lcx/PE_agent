"""故障注入：模拟真实环境中的扰动，测 Agent 的鲁棒性。

Claw-Eval 的关键发现：错误注入会显著拉低可靠性（Pass³ 最多暴跌 24 个百分点）。
所以评测必须主动注入「接口失败 / 日志噪声 / 越权输入」等扰动，看 Agent 能否恢复。

初版提供两类注入（后续可扩展）：
- tool_failure : 让指定工具的首次调用返回失败（测重试/换策略能力）；
- log_noise    : 给日志观察注入噪声（测信息筛选能力）。
"""
from __future__ import annotations

from typing import Any

INJECTION_TYPES = ["tool_failure", "log_noise"]


def inject_tool_failure(tool_name: str, fail_times: int = 1) -> dict[str, Any]:
    """返回一个「工具失败」注入描述，供评测运行器消费。"""
    return {"type": "tool_failure", "tool": tool_name, "fail_times": fail_times}


def inject_log_noise(noise: str = "random gibberish line") -> dict[str, Any]:
    """返回一个「日志噪声」注入描述。"""
    return {"type": "log_noise", "noise": noise}
