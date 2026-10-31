"""FastAPI 请求/响应模型（Pydantic v2）。"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    goal: str = Field(..., description="救援目标，如：开机进入 grub rescue 无法启动")


class ChatResponse(BaseModel):
    finished: bool
    final_answer: str
    trajectory: list[dict[str, Any]] = Field(default_factory=list)


class SkillCreateRequest(BaseModel):
    name: str
    description: str = ""
    steps: list[dict[str, Any]] = Field(
        ..., description='如 [{"tool": "check_log", "params": {...}}, ...]'
    )
    risk_level: Literal["read_only", "low", "medium", "high"] = "medium"
    permission: Literal["public", "restricted", "admin"] = "restricted"


class SkillInfo(BaseModel):
    name: str
    version: str
    description: str
    risk_level: str
    permission: str
    tags: list[str] = Field(default_factory=list)


class EvalResponse(BaseModel):
    task_id: str
    finished: bool
    metrics: dict[str, float]
    trajectory: list[dict[str, Any]] = Field(default_factory=list)
