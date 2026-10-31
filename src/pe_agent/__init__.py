"""PE_saver_agent —— PE 盘系统修复助手 Agent 化项目。

把一个"规则驱动的系统救援工具"升级为"LLM 驱动的系统运维 Agent"，
完整展示 Agent 闭环：感知 → 规划 → 工具调用 → 反思 → 迭代。

模块总览：
- core         : 配置、LLM 抽象（真实模型 + 离线 FakeLLM）、Prompt 模板
- graph        : LangGraph 状态机（ReAct 主循环）
- memory       : 短期记忆（轨迹缓冲）+ 长期记忆（向量库）
- rag          : 历史故障案例检索增强
- skills       : Skill 框架雏形（注册 / 管理 / 运行 + 安全校验）
- tools        : 系统工具（挂载 / 修引导 / 查日志 / 修文件系统 …）
- reflection   : Reflexion 式反思模块
- evaluation   : ClawEval 风格评测 + OpenJudge 风格 Grader
- security     : A.I.G 风格安全管控（输入 / 工具 / 输出三道闸）
- api          : FastAPI 服务层
"""

__version__ = "0.1.0"
