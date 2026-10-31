"""FastAPI 服务入口。

启动：uvicorn pe_agent.api.main:app --reload
（先 `pip install -e .` 或设 PYTHONPATH=src）
"""
from __future__ import annotations

from fastapi import FastAPI

from pe_agent.api.routes import build_router
from pe_agent.config import get_settings
from pe_agent.graph.agent_loop import RepairAgent

# 模块级单例：整个服务共用一个 Agent（含其记忆/技能/护栏状态）
_agent = RepairAgent()


def create_app() -> FastAPI:
    app = FastAPI(
        title="PE 盘系统修复助手 Agent",
        description="LLM 驱动的系统运维 Agent：LangGraph 主循环 + RAG + Skill 框架 + 安全管控",
        version="0.1.0",
    )
    app.include_router(build_router(_agent))
    return app


app = create_app()


def main() -> None:
    import uvicorn
    s = get_settings()
    uvicorn.run("pe_agent.api.main:app", host=s.app_host, port=s.app_port, reload=True)


if __name__ == "__main__":
    main()
