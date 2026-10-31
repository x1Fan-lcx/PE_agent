"""短期记忆：当前任务的对话 / 轨迹缓冲。

面试考点：Agent 的「短期记忆」本质是上下文窗口管理——
把多轮对话、工具调用结果按序压入有限缓冲，避免上下文溢出（context overflow），
是「上下文工程（context engineering）」最基础的一环。
"""
from __future__ import annotations

from typing import Any


class ShortTermMemory:
    """先进先出的轨迹缓冲，最多保留 max_turns 轮。"""

    def __init__(self, max_turns: int = 20) -> None:
        self._max_turns = max_turns
        self._buffer: list[dict[str, Any]] = []

    def add(self, role: str, content: str) -> None:
        self._buffer.append({"role": role, "content": content})
        self._trim()

    def add_tool_result(self, tool: str, result: str) -> None:
        self._buffer.append(
            {"role": "tool", "content": f"[{tool}] {result}"}
        )
        self._trim()

    def get_context(self, k: int | None = None) -> list[dict[str, str]]:
        """返回给 LLM 的最近 k 条消息（不含工具结果，工具结果另由 observation 汇总）。"""
        items = [m for m in self._buffer if m["role"] != "tool"]
        return items[-k:] if k else items

    def get_trajectory(self) -> list[dict[str, Any]]:
        """返回完整轨迹（含工具结果），供反思与评测使用。"""
        return list(self._buffer)

    def clear(self) -> None:
        self._buffer.clear()

    def _trim(self) -> None:
        if len(self._buffer) > self._max_turns * 2:
            self._buffer = self._buffer[-self._max_turns * 2:]
