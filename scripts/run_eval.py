"""评测脚本：对内置故障注入评测集跑一轮基线，输出三维度指标。

用法：python scripts/run_eval.py
"""
from __future__ import annotations

from pe_agent.evaluation import EVAL_TASKS, aggregate, compute_metrics
from pe_agent.graph.agent_loop import RepairAgent


def main() -> None:
    agent = RepairAgent()
    runs = []
    print(f"{'任务':<10} {'故障类型':<12} {'完成':<5} {'完成度':<6} "
          f"{'安全':<6} {'鲁棒':<6} {'综合分':<7}")
    print("-" * 62)
    for task in EVAL_TASKS:
        result = agent.run(task.goal)
        m = compute_metrics(task, result["trajectory"], result["finished"])
        runs.append(m)
        print(f"{task.id:<10} {task.fault_type:<12} "
              f"{'是' if result['finished'] else '否':<6} "
              f"{m['completion']:<6.0f} {m['safety']:<6.0f} "
              f"{m['robustness']:<6.0f} {m['task_score']:<7}")
    print("-" * 62)
    avg = aggregate(runs)
    print(f"平均综合分：{avg.get('task_score')}  |  通过率(≥75)：{avg.get('pass_rate')}%")


if __name__ == "__main__":
    main()
