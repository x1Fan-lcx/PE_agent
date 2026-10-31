"""FastAPI 路由。"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from pe_agent.api.schemas import (
    ChatRequest,
    ChatResponse,
    EvalResponse,
    SkillCreateRequest,
    SkillInfo,
)
from pe_agent.evaluation import EVAL_TASKS, compute_metrics
from pe_agent.graph.agent_loop import RepairAgent
from pe_agent.tools import list_tools


def build_router(agent: RepairAgent) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @router.post("/chat", response_model=ChatResponse)
    def chat(req: ChatRequest) -> ChatResponse:
        result = agent.run(req.goal)
        return ChatResponse(
            finished=result["finished"],
            final_answer=result["final_answer"],
            trajectory=result["trajectory"],
        )

    @router.get("/tools")
    def tools() -> list[dict]:
        return list_tools()

    @router.get("/skills", response_model=list[SkillInfo])
    def list_skills() -> list[SkillInfo]:
        return [SkillInfo(**s) for s in agent.registry.list()]

    @router.post("/skills", response_model=SkillInfo)
    def create_skill(req: SkillCreateRequest) -> SkillInfo:
        try:
            cls = agent.manager.create_skill(
                name=req.name,
                description=req.description,
                steps=req.steps,
                risk_level=req.risk_level,
                permission=req.permission,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return SkillInfo(**cls.manifest.model_dump())

    @router.post("/skills/{name}/disable")
    def disable_skill(name: str) -> dict:
        if agent.registry.get(name) is None:
            raise HTTPException(status_code=404, detail="技能不存在")
        agent.manager.disable(name)
        return {"status": "disabled", "name": name}

    @router.post("/skills/{name}/enable")
    def enable_skill(name: str) -> dict:
        if agent.registry.get(name) is None:
            raise HTTPException(status_code=404, detail="技能不存在")
        agent.manager.enable(name)
        return {"status": "enabled", "name": name}

    @router.post("/eval", response_model=list[EvalResponse])
    def run_eval() -> list[EvalResponse]:
        """对内置评测集跑一轮（默认 FakeLLM 基线）。"""
        out: list[EvalResponse] = []
        for task in EVAL_TASKS:
            result = agent.run(task.goal)
            metrics = compute_metrics(task, result["trajectory"], result["finished"])
            out.append(EvalResponse(
                task_id=task.id,
                finished=result["finished"],
                metrics=metrics,
                trajectory=result["trajectory"],
            ))
        return out

    return router
