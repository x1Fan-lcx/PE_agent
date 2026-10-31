"""RAG 检索增强：历史故障案例检索 + 上下文注入。

思路：把「以前修过的相似故障」作为 few-shot 经验注入 prompt，
帮 LLM 更快定位根因、选择正确的修复工具（对应「从失败轨迹学习 / few-shot 优化」）。
"""
from __future__ import annotations

from typing import Any

from pe_agent.memory.long_term import LongTermMemory

# 种子案例：模拟历史积累的故障知识（初版内置；生产可来自真实工单/评测轨迹沉淀）
SEED_CASES: list[dict[str, Any]] = [
    {
        "text": "开机黑屏报 grub rescue，找不到 EFI 目录：先挂载根分区，重装 grub 到磁盘即可修复。",
        "metadata": {"fault_type": "boot", "fix": "repair_boot"},
    },
    {
        "text": "系统启动卡住，日志显示 EXT4-fs error：需先卸载分区，运行 fsck 修复文件系统后重启。",
        "metadata": {"fault_type": "filesystem", "fix": "repair_filesystem"},
    },
    {
        "text": "进不了系统提示 /boot 挂载失败：检查 /etc/fstab 配置，修正错误的 UUID 后重试挂载。",
        "metadata": {"fault_type": "boot", "fix": "fix_fstab"},
    },
]


class FaultCaseRAG:
    """把长期记忆当作历史故障案例库，提供检索与上下文拼装。"""

    def __init__(self, memory: LongTermMemory | None = None) -> None:
        self._memory = memory or LongTermMemory()
        self._seeded = False

    def ensure_seeded(self) -> None:
        if not self._seeded:
            for c in SEED_CASES:
                self._memory.add(c["text"], c["metadata"])
            self._seeded = True

    def add_case(self, text: str, metadata: dict[str, Any] | None = None) -> None:
        self._memory.add(text, metadata)

    def retrieve(self, query: str, k: int = 3) -> list[dict[str, Any]]:
        self.ensure_seeded()
        return self._memory.search(query, k)

    def format_context(self, query: str, k: int = 3) -> str:
        """把检索到的相似案例拼成可注入 prompt 的文本。"""
        hits = self.retrieve(query, k)
        if not hits:
            return "（无相似历史案例）"
        lines = ["以下是历史相似故障及修复经验（few-shot 参考）："]
        for i, h in enumerate(hits, 1):
            meta = h["metadata"]
            lines.append(f"{i}. [{meta.get('fault_type', '?')}] {h['text']}")
        return "\n".join(lines)
