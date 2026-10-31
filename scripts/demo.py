"""离线演示：用 FakeLLM 跑通 Agent 闭环（无需 API key）。

用法：python scripts/demo.py
"""
from __future__ import annotations

from pe_agent.graph.agent_loop import RepairAgent


def main() -> None:
    agent = RepairAgent()

    goals = [
        "电脑开机进入 grub rescue 界面，无法启动系统",
        "系统启动卡住，内核日志报 EXT4-fs error",
        "系统报 /boot 挂载失败，无法继续启动",
    ]

    for goal in goals:
        print("=" * 64)
        print(f"目标：{goal}")
        result = agent.run(goal)
        print(f"是否完成：{result['finished']}  |  结论：{result['final_answer']}")
        print("执行轨迹（动作层）：")
        for t in result["trajectory"]:
            print(f"  · {t.get('action')}: {t.get('message', '')[:50]}")
            # 技能/工具内部审计轨迹
            audit = (t.get("data") or {}).get("audit")
            if audit:
                for step in audit:
                    print(f"      ↳ {step.get('tool')}: {step.get('message', '')[:40]}")
        print()


if __name__ == "__main__":
    main()
