# 06 · 方法提炼报告（面试追问防身）

> 本文回答：**「你引入了哪些方法？每个方法来自哪个项目？为什么用？」**
> 面试官追问「这个 idea 是抄的吗」「为什么这么设计」时，照这份答。

## 1. 方法来源清单

| # | 引入的方法/思想 | 来源项目 | 在本项目的位置 | 落地形式 |
|---|---|---|---|---|
| 1 | 图状态机编排 Agent | **LangGraph**（LangChain 团队） | `graph/agent_loop.py` | 4 节点 ReAct 状态机 |
| 2 | ReAct（Reason + Act） | **ReAct 论文**（Yao et al., 2022） | `graph/agent_loop.py` | 思考-行动交替的 JSON 决策 |
| 3 | 反思-重试闭环（Verbal RL） | **Reflexion**（Shinn et al., 2023） | `reflection/reflector.py` | 失败反思入记忆、下次检索复用 |
| 4 | 三维度端到端评测 + 故障注入 | **Claw-Eval**（阿里） | `evaluation/` | completion/safety/robustness + 注入扰动 |
| 5 | LLM-as-a-Judge + 黄金集校准 | **OpenJudge**（阿里云/AgentScope） | `evaluation/grader.py` | rubric 打分 + `validate_on_golden` |
| 6 | 技能安全扫描（T01–T09） | **腾讯朱雀 A.I.G** | `security/guard.py`、`skills/manager.py` | 三道闸 + `scan_skill_source` |
| 7 | 短期/长期记忆分层 | **Mem0 / Letta(MemGPT)** | `memory/` | 轨迹缓冲 + 向量库 |
| 8 | RAG few-shot 增强 | **RAG 经典范式**（Lewis et al., 2020） | `rag/retriever.py` | 检索历史案例注入 prompt |
| 9 | 结构化工具调用 | **MCP / function calling** | `tools/base.py` | name/description/params_schema 声明 |
| 10 | 自进化 Agent | **AlphaOperation**（你华师大） | 贯穿 reflection + evaluation | 失败轨迹 → 反思 → 数据飞轮 |

## 2. 每个方法的「一句话动机」（防追问）

1. **LangGraph**：我业务里的「分级故障诊断状态机」本质是规则版 Agent，用图状态机迁移最顺。
2. **ReAct**：让 LLM「边想边做」，每步输出可解析的 JSON 动作，而不是一段自由文本。
3. **Reflexion**：普通重试是盲目重复，反思是「失败后先归因再换策略」——和我 Self-Reflection 科研一脉相承。
4. **Claw-Eval**：Agent 不能只看结果，要看「做对、做安全、做稳」，所以三维度 + 故障注入。
5. **OpenJudge**：把评测从「打分」升级成「优化闭环」，评分可转奖励信号。
6. **A.I.G**：系统救援是高危场景，借鉴其 Skill 扫描的风险分类，落地为运行时三道闸。
7. **Mem0/Letta**：短期记忆管上下文，长期记忆跨会话沉淀经验。
8. **RAG**：故障诊断靠经验，把「历史修复案例」当 few-shot 注入，降低工具选择错误。
9. **MCP**：工具声明式暴露，LLM 结构化调用，大厂 JD 高频考点。
10. **AlphaOperation**：把失败轨迹转成改进信号，形成自进化闭环。

## 3. 「借鉴 vs 复刻」的边界（面试会问）

> 「我不是复刻这些项目，而是**提炼它们的核心做法，落到我自己的业务场景**：ClawEval 我借它的『三维度 + 故障注入』评分思想，但任务集是我自己设计的系统故障注入集；A.I.G 我借它的风险分类，但做的是防御侧而非红队扫描侧；Reflexion 我借它的『语言反思入记忆』，但打通了 RAG 实现自进化。每个方法我都能讲清楚『为什么用、怎么改、解决了我的什么问题』。」

## 4. 追问速查表

| 追问 | 答 |
|---|---|
| 这个项目是不是套模板？ | 不是，方法是公开论文/开源的，场景和评测集是我自己的系统救援业务 |
| 难点在哪？ | 高危场景的安全管控 + 故障注入评测 + 反思自进化闭环，不是调个 API |
| 你和别人比差异化？ | 别人做「通用 Agent demo」，我做「AI Agent 落地操作系统场景」，有真实工具集 + 可评测指标 + 安全管控 |
| 下一步？ | 接真实 MCP server、真实 LLM、LangSmith 观测、失败轨迹数据飞轮 |
