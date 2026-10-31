# 05 · 技术选型调研

> 本文回答：**为什么用 LangChain/LangGraph + FastAPI**，以及它如何匹配企业 JD 的热门技术栈。

## 1. Agent 框架选型对比

| 框架 | 定位 | 特点 | 为什么选/不选 |
|---|---|---|---|
| **LangGraph** | 图状态机编排 | 显式节点/边、可观测、可 checkpoint | ✅ **选中**：精确映射「分级故障诊断状态机」 |
| LangChain | 组件生态 | prompt/tool/chain 抽象全 | ✅ 用其 `langchain-core`/`langchain-openai` 作为底座 |
| AutoGen | 多 Agent 对话 | 微软出品，多智能体协作 | 后续多 Agent 阶段再引入 |
| CrewAI | 角色扮演多 Agent | 轻量、Role-based | 定位偏「角色协作」，非本项目核心 |
| Semantic Kernel | 企业编排 | 微软、.NET 友好 | 与 Python 栈不匹配 |
| LlamaIndex | RAG 数据框架 | 检索增强最强 | 本项目 RAG 简单，暂不引入 |

**结论**：LangGraph 的图状态机思想与麒麟的「分级故障诊断状态机」是同构的——状态机换成图、if-else 换成 LLM 节点，迁移成本最低、叙事最顺。

## 2. LLM 选型

- **Qwen3**：有 SFT + 蒸馏经验（Qwen3-8B/4B），OpenAI 兼容接口，成本低。
- **DeepSeek**：推理强（R1 类 test-time compute），备选。
- 通过 `llm_api_base` 统一 OpenAI 兼容接口，**换模型零改代码**（工厂模式 `get_llm()`）。

## 3. 服务层：为什么 FastAPI（而非 Flask/Django）

| 维度 | FastAPI | Flask | Django |
|---|---|---|---|
| 异步 | ✅ 原生 async | ❌ | ❌ |
| 自动文档 | ✅ Swagger/OpenAPI | 需插件 | ✅ |
| 类型校验 | ✅ Pydantic v2 | 手动 | ORM 层 |
| 性能 | 高（Starlette） | 中 | 中 |
| JD 匹配 | **后端/AI 岗高频词** | 一般 | 一般 |

**关键点**：FastAPI + Pydantic 是当前 AI 应用后端的事实标准（LangChain/OpenAI SDK 都兼容），且是后端岗 JD 高频词，能同时覆盖「Agent 岗」和「后端岗」。

## 4. 检索/记忆选型

- **初版**：纯 Python 余弦相似度（零依赖、离线可跑）。
- **生产**：Chroma（轻量）/ FAISS（高性能）/ Milvus（分布式），接口不变即可替换。

## 5. 评测/观测选型

- **自建评测**（`evaluation/`）：对齐 ClawEval/OpenJudge，可控、可讲。
- **LangSmith**（可选）：轨迹追踪 + 可视化，LLM 应用标配观测平台。
- 其他候选：Opik、Phoenix、Braintrust。

## 6. 与 JD 热词的映射

| JD 高频词 | 本项目对应 |
|---|---|
| LangChain / LangGraph | ✅ Agent Loop 底座 |
| RAG | ✅ 故障案例检索增强 |
| MCP | ✅ Tools 层（v0.2 封装为真实 MCP server）|
| Agent / 多轮对话 | ✅ 四节点决策闭环 |
| FastAPI | ✅ 服务层 |
| 向量数据库 | ✅ 长期记忆（可换 Chroma/FAISS）|
| 提示词工程 | ✅ 结构化决策/反思/评分模板 |
| 大模型评测 | ✅ ClawEval 风格 + LLM-as-Judge |

## 7. 面试问答要点

- **Q：为什么用 LangGraph？** A：图状态机和我的业务（分级故障诊断状态机）同构，且节点可观测、可回放、可 checkpoint，比手写 while 循环更可控。
- **Q：为什么 LangChain 之上还要 LangGraph？** A：LangChain 是组件（prompt/tool/chain），LangGraph 是编排（状态机）；复杂 Agent 需要显式的图结构来控制流程和终止条件。
- **Q：换模型方便吗？** A：OpenAI 兼容接口 + 工厂模式，改一个环境变量即可，Qwen/DeepSeek/vLLM 通吃。
- **Q：FastAPI 为什么合适？** A：原生异步、自动文档、Pydantic 类型校验，是 AI 应用后端事实标准，也覆盖后端岗技能要求。
