"""LLM 抽象层。

设计要点：
1. 统一接口 `ChatModel`，上层（Agent Loop / Reflection / Grader）只依赖接口，不依赖具体厂商。
2. 提供两个实现：
   - OpenAIChatModel : 走 OpenAI 兼容接口（Qwen / DeepSeek / vLLM / OpenAI 都行）。
   - FakeChatModel    : 离线确定性 mock，用于无 key 的 demo 与单元测试，保证 CI 可跑。
3. 通过 `get_llm()` 工厂按配置自动选择，业务代码无感知。
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any

from pe_agent.config import get_settings


class ChatModel(ABC):
    """对话模型统一接口。"""

    @abstractmethod
    def invoke(self, messages: list[dict[str, str]]) -> str:
        """输入 OpenAI 风格 messages，返回纯文本回复。"""


class OpenAIChatModel(ChatModel):
    """OpenAI 兼容接口实现（延迟导入 langchain-openai，避免离线环境硬依赖）。"""

    def __init__(self) -> None:
        s = get_settings()
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "使用真实 LLM 需要安装 langchain-openai：pip install langchain-openai"
            ) from e
        kwargs: dict[str, Any] = dict(
            model=s.llm_model,
            api_key=s.llm_api_key,
            base_url=s.llm_api_base,
            temperature=s.llm_temperature,
        )
        # DeepSeek 等模型的思考模式开关（关掉拿确定性 JSON）
        if s.llm_disable_thinking:
            kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
        self._model = ChatOpenAI(**kwargs)

    def invoke(self, messages: list[dict[str, str]]) -> str:
        resp = self._model.invoke(messages)
        return resp.content if isinstance(resp.content, str) else str(resp.content)


class FakeChatModel(ChatModel):
    """离线确定性 mock：根据 prompt 里的指令关键字返回固定 JSON 决策。

    目的：让「Agent Loop → 工具 → 反思」整条链路在没有真实模型时也能端到端跑通，
    用于本地开发、CI 冒烟测试与评测框架的"基线"对照。
    """

    def invoke(self, messages: list[dict[str, str]]) -> str:
        # 取最后一条用户/系统指令作为决策依据
        last = ""
        for m in reversed(messages):
            if m.get("role") in ("user", "system"):
                last = m.get("content", "")
                break

        # 评审 / 反思类：返回评分
        if "评分" in last or "打分" in last or "grader" in last.lower():
            return '{"score": 80, "reason": "mock judge: 工具选择正确，步骤合理"}'

        # 反思类：给出"成功"判定（初版固定成功，真实模型会做语义判断）
        if "反思" in last or "reflect" in last.lower():
            return '{"verdict": "success", "reason": "mock reflection: 已达成目标"}'

        # 规划类：按故障关键字路由到对应工具/技能（模拟一个"懂业务"的基线模型）。
        # 注意：只从「目标：」这一行提取真实目标做匹配，避免被 RAG 注入的历史案例文本污染。
        # 系统提示词首行也含"目标："，故取最后一次出现的「目标：」= 观察信息里的用户真实目标。
        goals = re.findall(r"目标：([^\n]+)", last)
        goal = goals[-1] if goals else last
        # 注意匹配顺序：挂载优先于引导，否则 "/boot 挂载失败" 会被 "boot" 子串误判为引导故障
        if any(k in goal for k in ("挂载", "mount")):
            return (
                '{"thought": "挂载失败，先挂载分区", "action": "mount_partition", '
                '"action_input": {"device": "/dev/sda1", "mount_point": "/mnt/sysroot"}}'
            )
        if any(k in goal for k in ("grub", "引导", "EFI", "rescue")):
            return (
                '{"thought": "引导故障，走 repair_boot 技能", "action": "repair_boot", '
                '"action_input": {"device": "/dev/sda", "root_device": "/dev/sda1"}}'
            )
        if any(k in goal for k in ("EXT4", "文件系统", "fsck", "filesystem", "损坏")):
            return (
                '{"thought": "文件系统损坏，走 repair_filesystem 技能", '
                '"action": "repair_filesystem", '
                '"action_input": {"device": "/dev/sda1", "fs_type": "ext4"}}'
            )
        return (
            '{"thought": "mock plan", "action": "read_log", '
            '"action_input": {"keyword": "error"}}'
        )


def get_llm() -> ChatModel:
    """工厂：有 key 用真实模型，否则用 Fake 模型。"""
    return OpenAIChatModel() if get_settings().use_real_llm else FakeChatModel()
