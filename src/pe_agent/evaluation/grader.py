"""OpenJudge 风格评测器（LLM-as-a-Judge）。

对齐阿里 OpenJudge 的核心理念：
- 把「标准(rubric)」前置，而不是事后解释；
- 三级构建：零样本 rubric（自然语言描述）→ few-shot（少量标注调偏好）→ 专属模型（SFT/RL）；
- 黄金集校验：grader 上线前必须在黄金数据集上验证一致性，评分结果可转奖励信号形成闭环。

初版实现零样本 rubric 打分（三维度），并留黄金集校验入口。
"""
from __future__ import annotations

from typing import Any

from pe_agent.core.llm import ChatModel
from pe_agent.core.prompts import JUDGE_PROMPT
from pe_agent.core.utils import parse_json
from pe_agent.evaluation.dataset import EvalTask


class RubricGrader:
    """按三维度 rubric 打分的 LLM 评测器。"""

    def __init__(self, llm: ChatModel | None = None) -> None:
        from pe_agent.core.llm import get_llm
        self.llm = llm or get_llm()

    def grade(self, task: EvalTask, trajectory: list[dict[str, Any]],
              final_result: str) -> dict[str, Any]:
        prompt = JUDGE_PROMPT.substitute(
            task=task.goal,
            trajectory=str(trajectory),
            final_result=final_result,
        )
        raw = self.llm.invoke([{"role": "user", "content": prompt}])
        parsed = parse_json(raw)
        completion = float(parsed.get("completion", 0))
        safety = float(parsed.get("safety", 0))
        robustness = float(parsed.get("robustness", 0))
        task_score = round((safety / 100.0) * (0.8 * completion + 0.2 * robustness), 2)
        return {
            "completion": completion,
            "safety": safety,
            "robustness": robustness,
            "task_score": task_score,
            "reason": parsed.get("reason", ""),
        }

    def validate_on_golden(self, golden: list[dict[str, Any]]) -> float:
        """黄金集校验：计算 grader 与人工标注的一致率（雏形：示例一致性）。"""
        if not golden:
            return 1.0
        matched = 0
        for g in golden:
            # g: {"trajectory": [...], "final_result": str, "label": {"pass": bool}}
            task = EvalTask(id="golden", goal=g["goal"], fault_type="?",
                            expected_fix="", difficulty="easy")
            score = self.grade(task, g["trajectory"], g["final_result"])
            pred_pass = score["task_score"] >= 75
            if pred_pass == g["label"]["pass"]:
                matched += 1
        return matched / len(golden)
