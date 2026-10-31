"""Agent Loop —— LangGraph 状态机（ReAct 主循环）。

闭环：观察(observe) → 规划(plan) → 执行(act) → 反思(reflect) → 迭代回到观察。

这是麒麟「分级故障诊断状态机」的 Agent 化：
把硬编码 if-else 换成 LLM 决策，再加一层「反思-重试」闭环。

面试考点：
- 为什么用图而不是 while True？—— 状态机显式化，节点可插拔、可观测、可断点续跑，
  每个节点的输入输出都是可审计的状态（对齐 Claw-Eval「执行过程可审计」）。
- 条件边怎么决定继续还是结束？—— 反思节点给 verdict，叠加步数上限(max_iterations)兜底防失控。
"""
from __future__ import annotations

from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from pe_agent.config import get_settings
from pe_agent.core.llm import ChatModel, get_llm
from pe_agent.core.prompts import REFLECT_PROMPT, SYSTEM_PROMPT
from pe_agent.core.utils import parse_json
from pe_agent.graph.state import AgentState
from pe_agent.memory.short_term import ShortTermMemory
from pe_agent.rag.retriever import FaultCaseRAG
from pe_agent.security.guard import AgentGuard
from pe_agent.skills import (
    SkillManager,
    SkillRegistry,
    SkillRuntime,
    build_default_skill_system,
)
from pe_agent.tools import get_tool, list_tools


class RepairAgent:
    """系统救援 Agent：装配依赖并编译 LangGraph 图。"""

    def __init__(
        self,
        llm: ChatModel | None = None,
        rag: FaultCaseRAG | None = None,
        short_memory: ShortTermMemory | None = None,
    ) -> None:
        self.settings = get_settings()
        self.llm = llm or get_llm()
        self.rag = rag or FaultCaseRAG()
        self.short_memory = short_memory or ShortTermMemory()
        self.guard = AgentGuard()
        self.registry: SkillRegistry
        self.manager: SkillManager
        self.runtime: SkillRuntime
        self.registry, self.manager, self.runtime = build_default_skill_system()
        self.graph = self._build()

    # ------------------------------------------------------------------ 构图
    def _build(self):
        g = StateGraph(AgentState)
        g.add_node("observe", self._observe)
        g.add_node("plan", self._plan)
        g.add_node("act", self._act)
        g.add_node("reflect", self._reflect)
        g.add_edge(START, "observe")
        g.add_edge("observe", "plan")
        g.add_edge("plan", "act")
        g.add_edge("act", "reflect")
        g.add_conditional_edges(
            "reflect",
            self._should_continue,
            {"continue": "observe", "end": END},
        )
        return g.compile()

    # ------------------------------------------------------------------ 节点
    def _observe(self, state: AgentState) -> dict[str, Any]:
        """观察：汇总「系统观察 + 已执行结果」，并用 RAG 检索相似历史案例注入。"""
        goal = state["goal"]
        rag_ctx = self.rag.format_context(goal, k=3)
        traj = state.get("trajectory", [])
        history = "\n".join(
            f"- {t.get('action')}: {t.get('message', '')}" for t in traj[-6:]
        ) or "（尚无执行记录）"
        observations = (
            f"目标：{goal}\n\n历史执行记录：\n{history}"
        )
        return {"observations": observations, "rag_context": rag_ctx}

    def _plan(self, state: AgentState) -> dict[str, Any]:
        """规划：LLM 依据工具清单 + RAG 上下文 + 观察信息，决策下一步动作。"""
        manifest = "\n".join(
            f"- {t['name']}: {t['description']} (risk={t['risk_level']})"
            for t in list_tools()
        )
        skill_manifest = "\n".join(
            f"- {s['name']}: {s['description']} (risk={s['risk_level']})"
            for s in self.registry.list()
        )
        prompt = SYSTEM_PROMPT.substitute(
            tool_manifest=manifest + "\n\n可用技能(Skill)：\n" + skill_manifest,
            rag_context=state.get("rag_context", ""),
            observations=state.get("observations", ""),
        )
        messages = [{"role": "system", "content": prompt}]
        raw = self.llm.invoke(messages)
        action = parse_json(raw)
        self.guard.audit({"trace_id": "", "node": "plan", "action": action.get("action")})
        return {"pending_action": action}

    def _act(self, state: AgentState) -> dict[str, Any]:
        """执行：按动作名解析为工具或技能，走安全护栏后执行。"""
        action = state.get("pending_action", {})
        name = action.get("action", "finish")
        params = action.get("action_input", {})

        next_step = state.get("step", 0) + 1

        # 终止动作
        if name == "finish":
            summary = params.get("summary", "任务结束")
            return {
                "finished": True,
                "final_answer": summary,
                "step": next_step,
                "trajectory": [{"action": "finish", "message": summary}],
            }

        # 输入护栏（动作名/参数防注入）
        dec = self.guard.check_input(f"{name} {params}")
        if not dec.allowed:
            return self._fail(name, f"被安全护栏拦截: {dec.reason}", next_step)

        # 优先解析为工具，其次解析为技能
        tool = get_tool(name)
        if tool is not None:
            gd = self.guard.check_tool_call(name, params, tool.risk_level)
            if not gd.allowed:
                return self._fail(name, f"工具被拦截: {gd.reason}", next_step)
            result = tool.run(**params)
            self.guard.audit({"trace_id": "", "node": "act", "tool": name,
                              "allowed": True, "success": result.success})
            return self._record(name, result.message, result.success, result.data, next_step)

        skill_cls = self.registry.get(name)
        if skill_cls is not None:
            if not self.manager.is_enabled(name):
                return self._fail(name, f"技能 {name} 已被禁用", next_step)
            result = self.runtime.execute(skill_cls(), params)
            return self._record(name, result.message, result.success, result.data, next_step)

        return self._fail(name, "未知动作：既不是工具也不是技能", next_step)

    def _reflect(self, state: AgentState) -> dict[str, Any]:
        """反思：LLM 判定上一步是否成功 / 是否继续（Reflexion 的「语言反馈」）。"""
        if state.get("finished"):
            return {"reflection": "success"}
        traj = state.get("trajectory", [])
        last = traj[-1] if traj else {}
        prompt = REFLECT_PROMPT.substitute(
            goal=state["goal"],
            trajectory=str(traj),
            observation=str(last),
        )
        raw = self.llm.invoke([{"role": "user", "content": prompt}])
        verdict = parse_json(raw).get("verdict", "continue")
        finished = verdict == "success"
        return {
            "reflection": verdict,
            "finished": finished,
            "final_answer": last.get("message", "") if finished else "",
        }

    # ------------------------------------------------------------------ 路由
    def _should_continue(self, state: AgentState) -> Literal["continue", "end"]:
        if state.get("finished") or state.get("step", 0) >= self.settings.max_iterations:
            return "end"
        return "continue"

    # ------------------------------------------------------------------ 辅助
    def _record(self, name: str, message: str, success: bool,
                data: dict[str, Any] | None = None, step: int = 1) -> dict[str, Any]:
        return {
            "step": step,
            "trajectory": [{"action": name, "message": message,
                            "success": success, "data": data or {}}],
            "observations": f"{name}: {message}",
        }

    def _fail(self, name: str, reason: str, step: int = 1) -> dict[str, Any]:
        self.guard.audit({"trace_id": "", "node": "act", "action": name,
                          "blocked": True, "reason": reason})
        return {
            "step": step,
            "trajectory": [{"action": name, "message": reason, "success": False}],
            "observations": f"{name}: {reason}",
        }

    # ------------------------------------------------------------------ 对外
    def run(self, goal: str, initial_observations: str = "") -> dict[str, Any]:
        """端到端运行一次救援任务，返回最终状态。"""
        init: AgentState = {
            "goal": goal,
            "observations": initial_observations or f"目标：{goal}",
            "trajectory": [],
            "step": 0,
            "finished": False,
            "final_answer": "",
            "reflection": "",
        }
        final = self.graph.invoke(init)
        return {
            "goal": goal,
            "finished": final.get("finished", False),
            "final_answer": final.get("final_answer", ""),
            "trajectory": final.get("trajectory", []),
            "audit": self.guard.audit_log,
        }
