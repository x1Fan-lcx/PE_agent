"""评测子包：故障注入评测集 + ClawEval 三维度指标 + OpenJudge 风格 grader。"""
from pe_agent.evaluation.dataset import EvalTask, EVAL_TASKS
from pe_agent.evaluation.fault_inject import (
    INJECTION_TYPES,
    inject_log_noise,
    inject_tool_failure,
)
from pe_agent.evaluation.grader import RubricGrader
from pe_agent.evaluation.metrics import aggregate, compute_metrics

__all__ = [
    "EvalTask", "EVAL_TASKS",
    "INJECTION_TYPES", "inject_log_noise", "inject_tool_failure",
    "RubricGrader", "compute_metrics", "aggregate",
]
