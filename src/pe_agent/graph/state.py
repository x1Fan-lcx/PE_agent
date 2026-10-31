"""Agent 状态定义（LangGraph StateGraph 的共享状态）。

字段说明：
- goal        : 本次救援目标（用户输入）
- observations: 当前观察信息（系统状态 + 已执行结果 + RAG 检索上下文）
- trajectory  : 完整轨迹（动作 + 结果），用 operator.add 追加——供反思/评测/审计回放
- pending_action: LLM 刚决策出的下一步动作（plan 产出，act 消费）
- finished / final_answer: 终止条件与最终结论
"""
from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class AgentState(TypedDict, total=False):
    goal: str
    observations: str
    rag_context: str
    trajectory: Annotated[list[dict[str, Any]], operator.add]
    pending_action: dict[str, Any]
    step: int
    finished: bool
    final_answer: str
    reflection: str
