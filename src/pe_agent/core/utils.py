"""通用工具函数。"""
from __future__ import annotations

import json
import re
from typing import Any


def parse_json(text: str) -> dict[str, Any]:
    """从 LLM 输出中稳健地提取 JSON（容忍 markdown 代码块与前后缀文本）。"""
    text = text.strip()
    # 去掉 ```json ... ``` 包裹
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    # 取第一个 { 到最后一个 } 的片段
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 兜底：正则抓 key: value（宽松解析）
        return _loose_parse(text)


def _loose_parse(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in ("thought", "action", "verdict", "reason", "summary", "score"):
        m = re.search(rf'"{key}"\s*:\s*"([^"]*)"', text)
        if m:
            out[key] = m.group(1)
    return out or {"action": "finish", "action_input": {}}
