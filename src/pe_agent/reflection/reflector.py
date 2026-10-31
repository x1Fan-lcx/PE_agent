"""Reflexion 反思模块（语言强化学习）。

Reflexion（Shinn et al., 2023）核心：Agent 失败后不直接重试，
而是先用语言模型「自我反思」——把失败原因写成一段文本反馈，
存入记忆，下一次尝试时检索这些反思来改进策略。

本模块把「反思」与「长期记忆 + RAG」打通，形成自进化闭环：
  失败 → 反思(reflect) → 写入长期记忆(store) → 下次检索(retrieve) → 决策更准。
这正是你华师大科研 Self-Reflection Attribution 的工程化落地。
"""
from __future__ import annotations

from string import Template
from typing import Any

from pe_agent.core.llm import ChatModel
from pe_agent.memory.long_term import LongTermMemory

_REFLECT_SELF_PROMPT = Template("""你刚执行了一次系统修复任务但未成功。请反思失败原因，并总结一条可复用的经验。

目标：$goal
执行轨迹：$trajectory

请输出 JSON：
{"reflection": "一句话反思：哪一步做错了、为什么、下次应该怎么做"}
""")


class ReflexionModule:
    """负责生成反思、持久化反思、检索历史反思。"""

    def __init__(self, llm: ChatModel | None = None,
                 memory: LongTermMemory | None = None) -> None:
        from pe_agent.core.llm import get_llm
        self.llm = llm or get_llm()
        self.memory = memory or LongTermMemory()

    def reflect(self, goal: str, trajectory: list[dict[str, Any]],
                success: bool) -> str:
        """对一次执行生成反思文本（失败时才有价值，成功也可总结经验）。"""
        if success:
            return "本次修复成功，无需反思。"
        raw = self.llm.invoke([{
            "role": "user",
            "content": _REFLECT_SELF_PROMPT.substitute(goal=goal, trajectory=str(trajectory)),
        }])
        from pe_agent.core.utils import parse_json
        return parse_json(raw).get("reflection", raw)

    def store(self, reflection: str, metadata: dict[str, Any] | None = None) -> None:
        """把反思写入长期记忆，供 RAG 后续检索。"""
        meta = metadata or {}
        meta["kind"] = "reflection"
        self.memory.add(reflection, meta)

    def retrieve(self, goal: str, k: int = 3) -> list[dict[str, Any]]:
        """检索与当前目标相关的历史反思。"""
        return [r for r in self.memory.search(goal, k) if r["metadata"].get("kind") == "reflection"]
